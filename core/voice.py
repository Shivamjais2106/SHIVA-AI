"""
Voice Engine for S.H.I.V.A.
- Text-to-Speech (TTS): High-Definition Edge-TTS Neural Voice Engine
  Supports multiple crystal-clear neural voices (Prabhat, Ryan, Christopher, Neerja, Madhur)
- Speech-to-Text (STT): Microphone recognition with ambient noise cancellation
"""

import os
import re
import asyncio
import time
import hashlib
import threading
from pathlib import Path
from typing import Optional, Dict, List
import pygame
import speech_recognition as sr
import edge_tts

from config import CACHE_DIR, VOICE_NAME, VOICE_RATE, VOICE_PITCH, VOICE_VOLUME, USER_TITLE, ASSISTANT_NAME


def clean_text_for_speech(text: str) -> str:
    """
    Cleans markdown, code blocks, URLs, emojis, bullet numbers (1., 2.),
    and technical logs so Edge-TTS produces natural, human-like executive speech.
    """
    if not text:
        return ""

    # 1. Remove markdown code blocks completely
    cleaned = re.sub(r"```[\s\S]*?```", "", text)
    # 2. Remove inline code backticks but preserve inner text
    cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)

    # 3. Strip byte string wrappers like b'...' or b"..."
    cleaned = re.sub(r"\bb['\"]([^'\"]*)['\"]", r"\1", cleaned)

    # 4. Remove process instance termination logs e.g. "(16 process instance(s) terminated)"
    cleaned = re.sub(r"\(\s*\d+\s*process\s*instance\w*\s*terminated\s*\)", "", cleaned, flags=re.IGNORECASE)

    # 5. Remove image/link bracket annotations e.g. [image: Google] or [link: ...]
    cleaned = re.sub(r"\[image:[^\]]*\]", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\[link:[^\]]*\]", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", cleaned)

    # 6. Remove error codes or brackets like [AUTHENTICATIONFAILED]
    cleaned = re.sub(r"\[[A-Z_\s]{3,}\]", "", cleaned)

    # 7. Remove raw URLs completely from speech so TTS doesn't read http/links
    cleaned = re.sub(r"http[s]?://\S+", "", cleaned)

    # 8. Strip list numbering at the start of lines or within text (e.g. "1. ", "2. ", "1) ")
    # This prevents the robot from saying "One dot" or "One Security Alert"
    cleaned = re.sub(r"(?m)^\s*\d+[\.\)]\s+", "", cleaned)
    cleaned = re.sub(r"\s+\d+[\.\)]\s+(?=[A-Za-z])", " ", cleaned)

    # 9. Strip bullet markers and markdown symbols
    cleaned = re.sub(r"[•\-\*\+–—~_#\^\|\<\>\[\]]", " ", cleaned)

    # 10. Strip robotic key-value headers (e.g. "Sender:", "From:", "Subject:", "Context:", "Preview:")
    cleaned = re.sub(r"\b(Sender|From|Subject|Context|Preview|Date|Status|Category|Summary)\s*:\s*", "", cleaned, flags=re.IGNORECASE)

    # 11. Remove all emojis (unicode ranges) so TTS doesn't read out emoji names
    emoji_pattern = re.compile(
        "["
        "\U00010000-\U0010ffff"
        "\u2600-\u27ff"
        "\u2300-\u23ff"
        "\u2b50-\u2b55"
        "\u200d"
        "\ufe0f"
        "]+",
        flags=re.UNICODE
    )
    cleaned = emoji_pattern.sub("", cleaned)

    # 12. Remove remaining stray parentheses
    cleaned = re.sub(r"[\(\)]", " ", cleaned)

    # 13. Break phone numbers into rhythmic groups for natural spoken tempo
    cleaned = re.sub(r"(\+?\d{2})(\d{5})(\d{5})", r"\1 \2 \3", cleaned)

    # 14. Pronounce acronyms cleanly
    cleaned = re.sub(r"\bvscode\b", "V S Code", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bshiva\b", "Shiva", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bapi\b", "A P I", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\bide\b", "I D E", cleaned, flags=re.IGNORECASE)

    # 15. Clean up duplicate punctuation and collapse whitespace
    cleaned = re.sub(r"\s*([,\.\?!])\s*", r"\1 ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


class ShivaVoice:
    """Manages crystal-clear neural speech synthesis (TTS) and microphone listening (STT)."""

    AVAILABLE_VOICES: Dict[str, str] = {
        "prabhat": "en-IN-PrabhatNeural",        # Clear Indian English Male (Best for Hinglish + English)
        "ryan": "en-GB-RyanNeural",              # Sharp British Male (Jarvis Style)
        "christopher": "en-US-ChristopherNeural",# Deep Authoritative Male (AI Butler Style)
        "neerja": "en-IN-NeerjaNeural",          # Expressive Indian English Female
        "guy": "en-US-GuyNeural",                # Conversational American Male
        "madhur": "hi-IN-MadhurNeural",          # Fluent Hindi / Hinglish Male
        "swara": "hi-IN-SwaraNeural",            # Fluent Hindi / Hinglish Female
    }

    def __init__(self, voice_name: str = VOICE_NAME):
        self.voice_name = voice_name or "en-IN-PrabhatNeural"
        self.rate = VOICE_RATE or "+0%"
        self.pitch = VOICE_PITCH or "+0Hz"
        self.volume = VOICE_VOLUME or "+0%"

        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8

        # Initialize pygame audio mixer with high-fidelity studio settings
        try:
            pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=1024)
            pygame.mixer.init()
        except Exception:
            try:
                pygame.mixer.init()
            except Exception as e:
                print(f"[Warning] Pygame mixer init failed: {e}")

    def set_voice(self, voice_key_or_name: str) -> str:
        """Dynamically switches SHIVA's voice model."""
        clean_key = voice_key_or_name.lower().strip()
        new_voice = self.AVAILABLE_VOICES.get(clean_key, voice_key_or_name)
        self.voice_name = new_voice
        return f"Voice persona updated to '{new_voice}', {USER_TITLE}! 🎙️"

    def get_available_voices(self) -> Dict[str, str]:
        """Returns the dictionary of curated neural voices."""
        return self.AVAILABLE_VOICES

    def _get_cached_audio_path(self, text: str) -> Path:
        """Returns deterministic path for cached neural speech audio."""
        cache_dir = CACHE_DIR / "tts_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        hash_key = hashlib.md5(f"{text}_{self.voice_name}_{self.rate}_{self.pitch}".encode("utf-8")).hexdigest()
        return cache_dir / f"{hash_key}.mp3"

    def prepare_audio(self, text: str) -> Optional[str]:
        """
        Pre-synthesizes the entire response into a single, seamless, continuous audio file.
        This completely eliminates:
        1. Waiting AFTER text is printed (pre-synthesizes while status spinner is active!)
        2. Awkward 2-4 second pauses between full stops (renders in one natural human take!).
        """
        if not text:
            return None

        speech_text = clean_text_for_speech(text)
        if not speech_text:
            return None

        try:
            cached_file = self._get_cached_audio_path(speech_text)
            if cached_file.exists():
                return str(cached_file)

            # Synthesize the entire response seamlessly in one continuous take
            communicate = edge_tts.Communicate(
                speech_text,
                voice=self.voice_name,
                rate=self.rate,
                pitch=self.pitch,
                volume=self.volume,
            )
            communicate.save_sync(str(cached_file))
            return str(cached_file)
        except Exception as e:
            print(f"[SHIVA Voice Prepare Error]: {e}")
            return None

    def play_audio_sync(self, audio_path: str):
        """Loads and plays an audio file synchronously (blocking until finished). Used in Voice Mode."""
        if not audio_path or not os.path.exists(audio_path):
            return
        if not pygame.mixer.get_init():
            return
        try:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()

            pygame.mixer.music.load(audio_path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(30)
            pygame.mixer.music.unload()
        except Exception as e:
            print(f"[SHIVA Playback Error]: {e}")

    def play_audio_async(self, audio_path: str):
        """Plays audio asynchronously in a background daemon thread for zero UI lag."""
        if not audio_path or not os.path.exists(audio_path):
            return
        threading.Thread(target=self.play_audio_sync, args=(audio_path,), daemon=True).start()

    def speak(self, text: str) -> None:
        """
        Synthesizes and speaks text continuously from start to finish
        with zero awkward delays between sentences.
        """
        audio_file = self.prepare_audio(text)
        if audio_file:
            self.play_audio_sync(audio_file)

    def listen(self, timeout: int = 5, phrase_time_limit: int = 10) -> Optional[str]:
        """
        Listens to microphone input and converts speech to text.
        Returns recognized string or None if silent / timed out.
        """
        try:
            with sr.Microphone() as source:
                # Adjust for ambient background noise
                self.recognizer.adjust_for_ambient_noise(source, duration=0.6)
                audio = self.recognizer.listen(
                    source,
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit,
                )
                # Recognize using Google free STT with Indian English accent support
                text = self.recognizer.recognize_google(audio, language="en-IN")
                return text.strip()
        except sr.WaitTimeoutError:
            return None
        except sr.UnknownValueError:
            return None
        except Exception as e:
            print(f"[Mic Error]: {e}")
            return None

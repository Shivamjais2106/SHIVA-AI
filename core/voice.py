"""
Voice Engine for S.H.I.V.A. (Phase 3)
- Text-to-Speech (TTS): Edge-TTS Neural Voice (Iron-Man Jarvis Vibe)
- Speech-to-Text (STT): Microphone recognition using SpeechRecognition
"""

import os
import re
import asyncio
import tempfile
import time
from pathlib import Path
from typing import Optional
import pygame
import speech_recognition as sr
import edge_tts

from config import CACHE_DIR, VOICE_NAME, USER_TITLE, ASSISTANT_NAME


def clean_text_for_speech(text: str) -> str:
    """Strips markdown code blocks, asterisks, urls, and symbols for clean spoken audio."""
    # Remove code blocks
    cleaned = re.sub(r"```[\s\S]*?```", "code block omitted.", text)
    # Remove inline code
    cleaned = re.sub(r"`.*?`", "", cleaned)
    # Remove URLs
    cleaned = re.sub(r"http[s]?://\S+", "link", cleaned)
    # Remove emojis and symbols
    cleaned = re.sub(r"[\*#_~\[\]\(\)\|•–—]", " ", cleaned)
    # Collapse whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


class ShivaVoice:
    """Manages speaking (TTS) and listening (STT) for S.H.I.V.A."""

    def __init__(self, voice_name: str = VOICE_NAME):
        self.voice_name = voice_name or "en-GB-RyanNeural"
        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = True
        self.recognizer.pause_threshold = 0.8
        self.speech_file = CACHE_DIR / "shiva_response.mp3"

        # Initialize pygame audio mixer
        try:
            pygame.mixer.init()
        except Exception as e:
            print(f"[Warning] Pygame mixer init failed: {e}")

    async def _generate_audio(self, text: str, output_path: str):
        """Asynchronously converts text to speech using edge-tts."""
        communicate = edge_tts.Communicate(text, self.voice_name)
        await communicate.save(output_path)

    def speak(self, text: str) -> None:
        """Speaks the response using neural TTS audio."""
        if not text:
            return

        speech_text = clean_text_for_speech(text)
        if not speech_text:
            return

        try:
            # Stop any ongoing playback
            if pygame.mixer.get_init() and pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
                pygame.mixer.music.unload()

            # Generate MP3 file
            audio_path = str(CACHE_DIR / f"speech_{int(time.time())}.mp3")
            asyncio.run(self._generate_audio(speech_text, audio_path))

            # Play audio
            if pygame.mixer.get_init():
                pygame.mixer.music.load(audio_path)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
                pygame.mixer.music.unload()

            # Clean up audio file
            try:
                if os.path.exists(audio_path):
                    os.remove(audio_path)
            except Exception:
                pass

        except Exception as e:
            print(f"[SHIVA Voice Output Error]: {e}")

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

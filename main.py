import sys
import threading
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich.table import Table

from config import ASSISTANT_NAME, ASSISTANT_FULL_NAME, USER_TITLE, USER_REAL_NAME, SPEECH_ENABLED, VOICE_NAME
from memory.memory_manager import MemoryManager
from core.brain import ShivaBrain
from core.voice import ShivaVoice

console = Console()


def print_banner(brain: ShivaBrain, voice: ShivaVoice, voice_active: bool):
    banner_text = f"""
  ███████╗██╗  ██╗██╗██╗   ██╗ █████╗        █████╗ ██╗
  ██╔════╝██║  ██║██║██║   ██║██╔══██╗      ██╔══██╗██║
  ███████╗███████║██║██║   ██║███████║█████╗███████║██║
  ╚════██║██╔══██║██║╚██╗ ██╔╝██╔══██║╚════╝██╔══██║██║
  ███████║██║  ██║██║ ╚████╔╝ ██║  ██║      ██║  ██║██║
  ╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝  ╚═╝  ╚═╝      ╚═╝  ╚═╝╚═╝
    """
    console.print(Panel(Text(banner_text, style="bold cyan"), subtitle=f"[bold green]{ASSISTANT_FULL_NAME}[/bold green]"))

    status_table = Table(show_header=False, box=None, padding=(0, 2))
    status_table.add_column("Key", style="bold yellow")
    status_table.add_column("Value", style="bold white")

    status_table.add_row("Operator", f"{USER_REAL_NAME} (Addressing as: [bold cyan]{USER_TITLE}[/bold cyan])")
    status_table.add_row("Memory Status", f"[bold green]Active[/bold green] (Resume & Workspaces Loaded)")
    
    api_status = "[bold green]Online (Gemini Flash + Direct Offline Engine)[/bold green]"
    status_table.add_row("Brain Engine", api_status)
    status_table.add_row(
        "Voice Engine",
        f"[bold green]Enabled ({VOICE_NAME})[/bold green]" if voice_active else "[bold red]Muted (Type 'voice on')[/bold red]"
    )
    status_table.add_row("Safety Policy", "[bold yellow]Git Push Banned | 2x Confirm Delete Guard[/bold yellow]")
    status_table.add_row(
        "Modes & Controls",
        "[cyan]'mic'[/cyan] for Voice Mode | [cyan]'voice on/off'[/cyan] | [cyan]'help'[/cyan] | [cyan]'exit'[/cyan]"
    )

    console.print(Panel(status_table, title="[bold cyan]SYSTEM DIAGNOSTICS & VOICE ENGINE[/bold cyan]", border_style="cyan"))
    console.print()


def show_help():
    table = Table(title="S.H.I.V.A. - Full Voice & Action Catalog", style="cyan")
    table.add_column("Command / Trigger", style="yellow")
    table.add_column("Action / Capability", style="white")

    table.add_row("mic / voice mode", "Activates live Microphone listening (talk to Shiva hands-free)")
    table.add_row("voice on / voice off", "Toggle whether Shiva speaks replies aloud")
    table.add_row("Hey Shiva, open LeetCode / GitHub / Portfolio", "Opens professional profiles & live portfolio in Chrome")
    table.add_row("Hey Shiva, close tab / close github on chrome", "Closes active browser tab without terminating Chrome")
    table.add_row("Hey Shiva, read emails / send email", "Checks Gmail inbox or composes emails")
    table.add_row("Hey Shiva, send whatsapp message / call", "Sends WhatsApp message or starts a call")
    table.add_row("Hey Shiva, simulate whatsapp / whatsapp bot", "Auto-responder with greeting & questions for unknown numbers")
    table.add_row("Hey Shiva, open TechnoKart in Antigravity", "Opens project in Antigravity IDE")
    table.add_row("Hey Shiva, open TechnoKart in VS Code", "Opens project in VS Code")
    table.add_row("Hey Shiva, check git status", "Checks branch, staged, modified, and untracked files (0 tokens)")
    table.add_row("Hey Shiva, commit files with message 'xyz'", "Runs git add . and git commit -m 'xyz' (0 tokens)")
    table.add_row("Hey Shiva, play / pause / next song", "Controls Spotify / Windows media playback")
    table.add_row("Hey Shiva, volume up / down / mute", "Adjusts master system audio")
    table.add_row("Hey Shiva, open Spotify / Chrome / Calc", "Opens any desktop application")
    table.add_row("Hey Shiva, close VS Code / Chrome", "Terminates application process on command")
    table.add_row("Hey Shiva, check battery and ram", "Live battery %, plugged status, CPU & RAM")
    table.add_row("profile", "Inspect Shiva's loaded memory about Boss")
    console.print(table)
    console.print()


def speak_in_background(voice: ShivaVoice, text: str):
    """Speaks text in a separate thread so console output stays snappy."""
    threading.Thread(target=voice.speak, args=(text,), daemon=True).start()


def run_voice_loop(brain: ShivaBrain, voice: ShivaVoice, memory: MemoryManager):
    """Continuous listening voice loop."""
    console.print(Panel(
        "[bold green]🎙️ VOICE MODE ACTIVATED[/bold green]\n"
        "Shiva is listening to your microphone...\n"
        "Speak your command, or say [bold yellow]'exit voice'[/bold yellow] / press [bold yellow]Ctrl+C[/bold yellow] to return to text.",
        border_style="green"
    ))
    voice.speak(f"Voice mode active. I am listening, {USER_TITLE}.")

    while True:
        try:
            console.print("[dim cyan]Listening...[/dim cyan]")
            heard_text = voice.listen(timeout=6, phrase_time_limit=10)

            if not heard_text:
                continue

            console.print(f"[bold yellow]🗣️ You:[/bold yellow] {heard_text}")

            if any(k in heard_text.lower() for k in ["exit voice", "stop voice", "text mode", "switch to text"]):
                console.print(f"[bold cyan]{ASSISTANT_NAME}:[/bold cyan] Switching back to text mode, {USER_TITLE}.\n")
                voice.speak("Switching to text mode, Boss.")
                break

            if heard_text.lower() in ["exit", "quit", "shutdown"]:
                console.print(f"[bold cyan]{ASSISTANT_NAME}:[/bold cyan] Shutting down, {USER_TITLE}!\n")
                voice.speak(f"Standing down, {USER_TITLE}.")
                sys.exit(0)

            with console.status(f"[bold cyan]{ASSISTANT_NAME} is processing...[/bold cyan]", spinner="dots"):
                response = brain.generate_response(heard_text)
                audio_path = voice.prepare_audio(response)

            console.print(f"\n[bold cyan]{ASSISTANT_NAME}:[/bold cyan] {response}\n")
            if audio_path:
                voice.play_audio_sync(audio_path)

        except KeyboardInterrupt:
            console.print("\n[yellow]Voice mode paused. Returning to text mode.[/yellow]\n")
            break
        except Exception as e:
            console.print(f"[red]Voice Error:[/red] {e}")


def main():
    memory = MemoryManager()
    brain = ShivaBrain(memory=memory)
    voice = ShivaVoice()
    voice_active = SPEECH_ENABLED

    print_banner(brain, voice, voice_active)

    greeting = (
        f"[bold cyan]{ASSISTANT_NAME}:[/bold cyan] Systems online, voice engine armed. "
        f"Awaiting instructions, [bold yellow]{USER_TITLE}[/bold yellow]!"
    )
    console.print(greeting)
    console.print()

    if voice_active:
        speak_in_background(voice, f"Systems online. Standing by for your command, {USER_TITLE}.")

    while True:
        try:
            user_input = Prompt.ask(f"[bold green]Hey {ASSISTANT_NAME}[/bold green]").strip()

            if not user_input:
                continue

            # Switch to continuous voice mode
            if user_input.lower() in ["mic", "voice", "voice mode", "listen"]:
                run_voice_loop(brain, voice, memory)
                continue

            # Toggle speech output
            if user_input.lower() in ["voice on", "enable voice"]:
                voice_active = True
                console.print(f"[bold green]Voice output enabled.[/bold green] {ASSISTANT_NAME} will now speak replies aloud.\n")
                voice.speak(f"Voice output enabled, {USER_TITLE}.")
                continue

            if user_input.lower() in ["voice off", "mute voice", "disable voice"]:
                voice_active = False
                console.print(f"[bold yellow]Voice output muted.[/bold yellow] {ASSISTANT_NAME} will now reply in text only.\n")
                continue

            # Switch voice model dynamically
            if user_input.lower().startswith("voice ") and user_input.lower() not in ["voice on", "voice off", "voice mode"]:
                v_target = user_input.lower().replace("voice", "").replace("switch to", "").replace("change to", "").replace("set", "").strip()
                msg = voice.set_voice(v_target)
                console.print(f"[bold green]{msg}[/bold green]\n")
                if voice_active:
                    voice.speak(msg)
                continue

            if user_input.lower() in ["voices", "list voices", "show voices"]:
                v_table = Table(title="Available Neural Voice Personas", style="cyan")
                v_table.add_column("Key / Trigger", style="yellow")
                v_table.add_column("Model Name", style="white")
                v_table.add_column("Character / Tone", style="green")
                v_table.add_row("voice prabhat", "en-IN-PrabhatNeural", "Natural Indian English (Best clarity & Hinglish)")
                v_table.add_row("voice ryan", "en-GB-RyanNeural", "British Jarvis Style (Sharp & authoritative)")
                v_table.add_row("voice christopher", "en-US-ChristopherNeural", "Deep AI Butler / Executive")
                v_table.add_row("voice neerja", "en-IN-NeerjaNeural", "Expressive Indian English Female")
                v_table.add_row("voice guy", "en-US-GuyNeural", "Conversational American Male")
                v_table.add_row("voice madhur", "hi-IN-MadhurNeural", "Fluent Hindi / Hinglish Male")
                console.print(v_table)
                continue

            if user_input.lower() in ["exit", "quit", "bye", "shutdown"]:
                console.print(f"\n[bold cyan]{ASSISTANT_NAME}:[/bold cyan] Standing down. Systems on standby, {USER_TITLE}!\n")
                if voice_active:
                    voice.speak(f"Standing down. Have a productive day, {USER_TITLE}!")
                break

            if user_input.lower() == "help":
                show_help()
                continue

            if user_input.lower() == "profile":
                user_info = memory.profile.get("user", {})
                career = memory.profile.get("career", {})
                skills = memory.profile.get("skills", {})
                
                info_table = Table(title=f"Memory Profile: {user_info.get('name')}", style="cyan")
                info_table.add_column("Category", style="yellow")
                info_table.add_column("Details", style="white")

                info_table.add_row("Current Role", str(career.get("current_role")))
                info_table.add_row("Top Languages", ", ".join(skills.get("languages", [])))
                info_table.add_row("Frontend", ", ".join(skills.get("frontend", [])))
                info_table.add_row("Backend", ", ".join(skills.get("backend", [])))
                console.print(info_table)
                continue

            with console.status(f"[bold cyan]{ASSISTANT_NAME} is processing...[/bold cyan]", spinner="dots"):
                response = brain.generate_response(user_input)
                audio_path = voice.prepare_audio(response) if voice_active else None

            console.print(f"\n[bold cyan]{ASSISTANT_NAME}:[/bold cyan] {response}\n")

            if voice_active and audio_path:
                voice.play_audio_async(audio_path)

        except KeyboardInterrupt:
            console.print(f"\n[bold cyan]{ASSISTANT_NAME}:[/bold cyan] Interrupted. Goodbye, {USER_TITLE}!\n")
            break
        except Exception as e:
            console.print(f"\n[bold red]Error:[/bold red] {e}\n")


if __name__ == "__main__":
    main()

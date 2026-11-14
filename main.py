import sys
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich.table import Table

from config import ASSISTANT_NAME, ASSISTANT_FULL_NAME, USER_TITLE, USER_REAL_NAME
from memory.memory_manager import MemoryManager
from core.brain import ShivaBrain

console = Console()


def print_banner(brain: ShivaBrain, memory: MemoryManager):
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
    
    api_status = "[bold green]Online (Gemini 2.5 Flash with Auto-Failover)[/bold green]" if brain.has_api_key() else "[bold red]API Key Missing (Check .env)[/bold red]"
    status_table.add_row("Brain Engine", api_status)
    status_table.add_row(
        "Action Skills",
        "[bold green]Full Desktop Access[/bold green] (VS Code, Antigravity, Terminal, Spotify, Chrome, 2x Safe Delete)"
    )
    status_table.add_row("Security Gate", "[bold yellow]Git Push Banned | 2-Step File Delete Guard[/bold yellow]")
    status_table.add_row("Commands", "[cyan]'exit'[/cyan] to quit | [cyan]'profile'[/cyan] for memory | [cyan]'help'[/cyan] for skills")

    console.print(Panel(status_table, title="[bold cyan]SYSTEM DIAGNOSTICS & PERMISSIONS[/bold cyan]", border_style="cyan"))
    console.print()


def show_help():
    table = Table(title="S.H.I.V.A. - Full Permission & Action Catalog", style="cyan")
    table.add_column("Module", style="yellow")
    table.add_column("Capability & Examples", style="white")

    table.add_row("IDEs & Projects", "Open in VS Code or Antigravity ('open TechnoKart in Antigravity')")
    table.add_row("App Management", "Open/Close ANY app ('launch Spotify', 'close VS Code', 'open Calculator')")
    table.add_row("Terminal & Shell", "Run dev commands ('git status', 'git add .', 'git commit -m \"...\"', 'npm run dev')")
    table.add_row("Git Security", "⛔ 'git push' is strictly BLOCKED. Boss pushes to remote manually.")
    table.add_row("Media & Music", "Control Spotify ('play/pause', 'next song', 'volume up/down', 'mute')")
    table.add_row("Chrome Web", "Google search, open websites, open GitHub / LeetCode profiles")
    table.add_row("File Operations", "List files, read source code, find & replace specific text in files")
    table.add_row("Deletion Guard", "⚠️ Strict 2-step verification required before deleting any file")
    table.add_row("System Health", "Live Battery %, CPU load, RAM usage metrics")
    console.print(table)
    console.print()


def main():
    memory = MemoryManager()
    brain = ShivaBrain(memory=memory)

    print_banner(brain, memory)

    greeting = (
        f"[bold cyan]{ASSISTANT_NAME}:[/bold cyan] All desktop permissions active under your strict command. "
        f"Awaiting instructions, [bold yellow]{USER_TITLE}[/bold yellow]!"
    )
    console.print(greeting)
    console.print()

    while True:
        try:
            user_input = Prompt.ask(f"[bold green]Hey {ASSISTANT_NAME}[/bold green]").strip()

            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit", "bye", "shutdown"]:
                console.print(f"\n[bold cyan]{ASSISTANT_NAME}:[/bold cyan] Standing down. Have a great day, {USER_TITLE}!\n")
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

            if user_input.lower().startswith("remember "):
                note = user_input[9:].strip()
                if note:
                    memory.add_note(note)
                    console.print(f"[bold cyan]{ASSISTANT_NAME}:[/bold cyan] Noted, {USER_TITLE}. Stored in long-term memory: '{note}'\n")
                continue

            with console.status(f"[bold cyan]{ASSISTANT_NAME} is executing...[/bold cyan]", spinner="dots"):
                response = brain.generate_response(user_input)

            console.print(f"\n[bold cyan]{ASSISTANT_NAME}:[/bold cyan] {response}\n")

        except KeyboardInterrupt:
            console.print(f"\n[bold cyan]{ASSISTANT_NAME}:[/bold cyan] Interrupted. Standing by, {USER_TITLE}!\n")
            break
        except Exception as e:
            console.print(f"\n[bold red]Error:[/bold red] {e}\n")


if __name__ == "__main__":
    main()

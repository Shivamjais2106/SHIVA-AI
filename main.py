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
    status_table.add_row("Memory Status", f"[bold green]Active[/bold green] (Resume & Projects Loaded)")
    
    api_status = "[bold green]Online (Gemini 2.5 Flash)[/bold green]" if brain.has_api_key() else "[bold red]API Key Missing (Check .env)[/bold red]"
    status_table.add_row("Brain Engine", api_status)
    status_table.add_row("Action Skills", "[bold green]Active[/bold green] (VS Code, Antigravity, Chrome, Files, 2x Safe Delete)")
    status_table.add_row("Commands", "[cyan]'exit'[/cyan] to quit | [cyan]'profile'[/cyan] for memory | [cyan]'help'[/cyan] for skills")

    console.print(Panel(status_table, title="[bold cyan]SYSTEM DIAGNOSTICS[/bold cyan]", border_style="cyan"))
    console.print()


def show_help():
    table = Table(title="S.H.I.V.A. - Action Capabilities", style="cyan")
    table.add_column("Category", style="yellow")
    table.add_column("Example Command", style="white")

    table.add_row("System Health", "Hey Shiva, check my battery and RAM status")
    table.add_row("Open in VS Code", "Hey Shiva, open TechnoKart in VS Code")
    table.add_row("Open in Antigravity", "Hey Shiva, open TechnoKart in Antigravity IDE")
    table.add_row("Chrome Web", "Hey Shiva, open Chrome and search React 19 tutorial")
    table.add_row("Developer Profiles", "Hey Shiva, open my GitHub profile / LeetCode")
    table.add_row("File Inspection", "Hey Shiva, what files are inside TechnoKart?")
    table.add_row("Read Code", "Hey Shiva, read the package.json of TechnoKart")
    table.add_row("Edit Code", "Hey Shiva, change port 3000 to 5000 in .env")
    table.add_row("Strict Safe Delete", "Enforces 2-step verification before deleting any file")
    console.print(table)
    console.print()


def main():
    memory = MemoryManager()
    brain = ShivaBrain(memory=memory)

    print_banner(brain, memory)

    greeting = (
        f"[bold cyan]{ASSISTANT_NAME}:[/bold cyan] Systems online, action skills armed. "
        f"Awaiting your command, [bold yellow]{USER_TITLE}[/bold yellow]!"
    )
    console.print(greeting)
    console.print()

    while True:
        try:
            user_input = Prompt.ask(f"[bold green]Hey {ASSISTANT_NAME}[/bold green]").strip()

            if not user_input:
                continue

            if user_input.lower() in ["exit", "quit", "bye", "shutdown"]:
                console.print(f"\n[bold cyan]{ASSISTANT_NAME}:[/bold cyan] Standing down. Systems on standby, {USER_TITLE}!\n")
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
                    console.print(f"[bold cyan]{ASSISTANT_NAME}:[/bold cyan] Understood, {USER_TITLE}. Stored in long-term memory: '{note}'\n")
                continue

            with console.status(f"[bold cyan]{ASSISTANT_NAME} is executing...[/bold cyan]", spinner="dots"):
                response = brain.generate_response(user_input)

            console.print(f"\n[bold cyan]{ASSISTANT_NAME}:[/bold cyan] {response}\n")

        except KeyboardInterrupt:
            console.print(f"\n[bold cyan]{ASSISTANT_NAME}:[/bold cyan] Interrupted. Goodbye, {USER_TITLE}!\n")
            break
        except Exception as e:
            console.print(f"\n[bold red]Error:[/bold red] {e}\n")


if __name__ == "__main__":
    main()

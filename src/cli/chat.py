#!/usr/bin/env python3
"""
CLI Chat Interface for IT Operations AI Agent.
Provides an interactive command-line interface to chat with the AI agent.
"""
import os
import sys
import click
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt
from dotenv import load_dotenv

# Add parent directory to path to import agent
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.agent.ai_agent import ITOperationsAgent

console = Console()


def print_welcome():
    """Print welcome message."""
    welcome_text = """
# IT Operations AI Assistant

Welcome to the IT Operations AI Assistant! I can help you with:

- **Add users to groups**: "Add john to the developers group"
- **Reboot VMs**: "Reboot the web-server VM"
- **Whitelist paths**: "Whitelist /opt/app/data for backup access"

Type your request in natural language, and I'll execute the appropriate action.

**Commands:**
- `exit` or `quit` - Exit the chat
- `clear` - Clear conversation history
- `help` - Show this help message
"""
    console.print(Panel(Markdown(welcome_text), title="Welcome", border_style="blue"))


def print_help():
    """Print help message."""
    help_text = """
# Available Commands

- **exit** or **quit** - Exit the chat application
- **clear** - Clear the conversation history and start fresh
- **help** - Show this help message

# Example Requests

- "Add user sarah to the admins group"
- "Please reboot vm-production-01"
- "I need to whitelist the path /var/log/app for monitoring"
- "Can you add mike to developers and also reboot test-server?"
"""
    console.print(Panel(Markdown(help_text), title="Help", border_style="green"))


@click.command()
@click.option(
    '--api-url',
    default='http://localhost:8000',
    help='Base URL for the IT Operations API',
    show_default=True
)
@click.option(
    '--api-key',
    default=None,
    help='Anthropic API key (or set ANTHROPIC_API_KEY env var)'
)
def main(api_url: str, api_key: str):
    """
    IT Operations AI Assistant - Interactive CLI Chat Interface

    Chat with an AI agent that can perform IT operations by calling appropriate APIs.
    """
    # Load environment variables from .env file if it exists
    load_dotenv()

    # Check for API key
    if not api_key and not os.environ.get("ANTHROPIC_API_KEY"):
        console.print(
            "[bold red]Error:[/bold red] ANTHROPIC_API_KEY not found. "
            "Please set it as an environment variable or use --api-key option.",
            style="red"
        )
        console.print("\nYou can set it by running:")
        console.print("  export ANTHROPIC_API_KEY='your-api-key-here'", style="yellow")
        sys.exit(1)

    # Initialize the agent
    try:
        agent = ITOperationsAgent(api_base_url=api_url, api_key=api_key)
        console.print(f"[green]✓[/green] Connected to API at {api_url}")
    except Exception as e:
        console.print(f"[bold red]Error initializing agent:[/bold red] {str(e)}", style="red")
        sys.exit(1)

    # Print welcome message
    print_welcome()

    # Main chat loop
    while True:
        try:
            # Get user input
            user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]")

            # Handle empty input
            if not user_input.strip():
                continue

            # Handle commands
            command = user_input.strip().lower()

            if command in ['exit', 'quit']:
                console.print("\n[yellow]Goodbye![/yellow]")
                break

            elif command == 'clear':
                agent.reset_conversation()
                console.print("[green]✓[/green] Conversation history cleared")
                continue

            elif command == 'help':
                print_help()
                continue

            # Process the message with the AI agent
            console.print("\n[bold magenta]Assistant[/bold magenta] (thinking...)", style="dim")

            try:
                response = agent.chat(user_input)

                # Clear the "thinking" line and print response
                console.print("\r[bold magenta]Assistant:[/bold magenta]")
                console.print(Panel(response, border_style="magenta", padding=(1, 2)))

            except Exception as e:
                console.print(f"[bold red]Error:[/bold red] {str(e)}", style="red")
                console.print(
                    "\n[yellow]Tip:[/yellow] Make sure the API server is running at "
                    f"{api_url}"
                )

        except KeyboardInterrupt:
            console.print("\n\n[yellow]Interrupted. Type 'exit' to quit or press Ctrl+C again.[/yellow]")
            try:
                # Give user a chance to exit gracefully
                import time
                time.sleep(0.5)
            except KeyboardInterrupt:
                console.print("\n[yellow]Goodbye![/yellow]")
                break

        except EOFError:
            console.print("\n[yellow]Goodbye![/yellow]")
            break


if __name__ == '__main__':
    main()

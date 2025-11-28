#!/usr/bin/env python3
"""
CLI Chat Interface for IT Operations AI Agent.
Technical, terminal-friendly interface with optional debug mode.
"""
import os
import sys
import click
from dotenv import load_dotenv

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.agent.ai_agent import ITOperationsAgent


def print_banner():
    """Print minimal banner."""
    print("=" * 60)
    print("IT OPERATIONS AI AGENT")
    print("=" * 60)
    print("Commands: exit, quit, clear, help, debug")
    print("=" * 60)
    print()


def print_help():
    """Print help message."""
    print("\nCOMMANDS:")
    print("  exit, quit    - Exit the agent")
    print("  clear         - Clear conversation history")
    print("  help          - Show this help")
    print("  debug         - Toggle debug mode (show reasoning logs)")
    print("\nAVAILABLE OPERATIONS:")
    print("  - Add user to group: 'Add <username> to <group>'")
    print("  - Reboot VM: 'Reboot <vm_name>'")
    print("  - Whitelist path: 'Whitelist <path>'")
    print("\nEXAMPLES:")
    print("  > Add Arjun to CloudOps group")
    print("  > Reboot appserver-14 vm")
    print("  > Whitelist /opt/data/uploads")
    print()


@click.command()
@click.option(
    '--api-url',
    default='http://localhost:8000',
    help='IT Operations API base URL'
)
@click.option(
    '--debug/--no-debug',
    default=False,
    help='Enable debug mode (show reasoning logs)'
)
def main(api_url: str, debug: bool):
    """
    IT Operations AI Agent - CLI Interface

    Technical, deterministic agent for IT automation.
    Uses Portkey with Bedrock Claude Opus 4.
    """
    # Load environment variables
    load_dotenv()

    # Check for required credentials
    if not os.environ.get("PORTKEY_API_KEY"):
        print("ERROR: PORTKEY_API_KEY not set")
        print("Set it in .env or export PORTKEY_API_KEY='your-key'")
        sys.exit(1)

    # Initialize agent
    try:
        agent = ITOperationsAgent(
            api_base_url=api_url,
            debug=debug
        )
        print(f"[OK] Connected to API at {api_url}")
        if debug:
            print("[DEBUG] Debug mode enabled - showing reasoning logs")
    except Exception as e:
        print(f"ERROR: Failed to initialize agent: {e}")
        sys.exit(1)

    # Print banner
    print_banner()

    # Debug mode toggle
    debug_mode = debug

    # Main loop
    while True:
        try:
            # Get user input
            user_input = input("> ").strip()

            if not user_input:
                continue

            # Handle commands
            cmd = user_input.lower()

            if cmd in ['exit', 'quit']:
                print("\nExiting.")
                break

            elif cmd == 'clear':
                agent.reset_conversation()
                print("[OK] Conversation cleared")
                continue

            elif cmd == 'help':
                print_help()
                continue

            elif cmd == 'debug':
                debug_mode = not debug_mode
                agent.debug = debug_mode
                status = "enabled" if debug_mode else "disabled"
                print(f"[OK] Debug mode {status}")
                continue

            # Process message
            if debug_mode:
                print("[AGENT] Processing...")

            response = agent.chat(user_input)

            # Print response
            print(f"\n{response}\n")

            # Show reasoning log in debug mode
            if debug_mode:
                reasoning_log = agent.get_reasoning_log()
                if reasoning_log:
                    print("[DEBUG] Reasoning Log:")
                    for log_entry in reasoning_log:
                        print(f"  {log_entry}")
                    print()

        except KeyboardInterrupt:
            print("\n\n[INTERRUPT] Press Ctrl+C again to exit, or type 'exit'")
            try:
                import time
                time.sleep(0.5)
            except KeyboardInterrupt:
                print("\nExiting.")
                break

        except EOFError:
            print("\nExiting.")
            break

        except Exception as e:
            print(f"ERROR: {e}")
            if debug_mode:
                import traceback
                traceback.print_exc()


if __name__ == '__main__':
    main()

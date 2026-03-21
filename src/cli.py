#!/usr/bin/env python3
"""CLI for interacting with the customer service agent backend."""

import argparse

import httpx

DEFAULT_URL = "http://localhost:8000"


def _show_draft(data: dict) -> str | None:
    """Show draft reply with metadata and prompt for action. Returns approved reply or None."""
    print("\n--- Draft Reply ---")
    print(data["reply"])
    print()

    confidence = data.get("confidence", "?")
    needs_review = data.get("needs_human_review", False)
    print(f"[Confidence: {confidence}] [Review: {'required' if needs_review else 'not required'}]")

    note = data.get("internal_note", "")
    if note:
        print(f"Internal note: {note}")

    actions = data.get("suggested_actions", [])
    if actions:
        print(f"Suggested actions: {', '.join(actions)}")

    print()
    while True:
        choice = input("[a]pprove  [e]dit  [r]eject > ").strip().lower()
        if choice in ("a", "approve"):
            return data["reply"]
        elif choice in ("e", "edit"):
            edited = input("Enter replacement reply: ").strip()
            return edited if edited else data["reply"]
        elif choice in ("r", "reject"):
            return None
        print("  Invalid choice. Use a/e/r.")


PAGE_SIZE = 20


def _show_history(url: str, business_id: str, customer_id: str):
    """Fetch and display conversation history with pagination, recent first."""
    try:
        resp = httpx.get(f"{url}/history/{business_id}/{customer_id}", timeout=10.0)
    except (httpx.ConnectError, httpx.TimeoutException):
        print("  Error: cannot connect to backend.")
        return

    if resp.status_code != 200:
        print(f"  Error: {resp.text}")
        return

    messages = resp.json()
    if not messages:
        print("  No history yet.\n")
        return

    # Reverse for recent-first
    messages = list(reversed(messages))
    total = len(messages)
    offset = 0

    while offset < total:
        page = messages[offset : offset + PAGE_SIZE]
        remaining = total - offset - len(page)

        print(f"\n  --- History ({offset + 1}-{offset + len(page)} of {total}, recent first) ---")
        print(f"  {'Datetime':<22} {'From':<10} Message")
        print(f"  {'-' * 22} {'-' * 10} {'-' * 40}")

        for msg in page:
            ts = msg.get("timestamp", "")
            if ts:
                # Truncate to seconds
                ts = ts[:19].replace("T", " ")
            sender = "customer" if msg.get("role") == "user" else "agent"
            text = msg.get("content", "")
            # Truncate long messages for table display
            if len(text) > 60:
                text = text[:57] + "..."
            print(f"  {ts:<22} {sender:<10} {text}")

        print()

        if remaining > 0:
            try:
                prompt = f"  {remaining} more messages. [n]ext page / [q]uit > "
                choice = input(prompt).strip().lower()
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if choice in ("n", "next", ""):
                offset += PAGE_SIZE
            else:
                break
        else:
            break


def _handle_command(cmd: str, business_id: str, customer_id: str, url: str):
    """Handle in-session /commands."""
    command = cmd.split()[0].lower()

    if command == "/help":
        print("\nCommands:")
        print("  /help       Show this help")
        print("  /info       Show current session info")
        print("  /history    Show conversation history")
        print("  quit        End session\n")

    elif command == "/info":
        print(f"\n  Business: {business_id}")
        print(f"  Customer: {customer_id}")
        print(f"  Backend:  {url}\n")

    elif command == "/history":
        _show_history(url, business_id, customer_id)

    else:
        print(f"  Unknown command: {command}. Type /help for available commands.\n")


def main():
    parser = argparse.ArgumentParser(description="Customer service agent CLI")
    parser.add_argument("--business", help="Business ID to use")
    parser.add_argument("--customer", help="Customer ID")
    parser.add_argument("--url", default=DEFAULT_URL, help=f"Backend URL (default: {DEFAULT_URL})")
    parser.add_argument(
        "--list-businesses", action="store_true", help="List available businesses and exit"
    )
    parser.add_argument(
        "--auto-approve", action="store_true", help="Skip draft review, print replies directly"
    )
    args = parser.parse_args()

    # List businesses and exit
    if args.list_businesses:
        try:
            resp = httpx.get(f"{args.url}/businesses", timeout=10.0)
            if resp.status_code == 200:
                for b in resp.json():
                    print(f"  {b['business_id']:<20} {b['name']}")
            else:
                print(f"Error: {resp.text}")
        except httpx.ConnectError:
            print(f"Error: cannot connect to backend at {args.url}. Is it running?")
        return

    # Require --business and --customer for interactive mode
    if not args.business:
        parser.error("--business is required (use --list-businesses to see available)")
    if not args.customer:
        parser.error("--customer is required")

    business_id = args.business
    customer_id = args.customer

    # Startup banner
    biz_name = business_id
    try:
        resp = httpx.get(f"{args.url}/businesses", timeout=5.0)
        if resp.status_code == 200:
            for b in resp.json():
                if b["business_id"] == business_id:
                    biz_name = b["name"]
                    break
    except (httpx.ConnectError, httpx.TimeoutException):
        pass

    print(f"\nConnected to {biz_name}")
    print(f"Customer: {customer_id}")
    mode = "auto-approve" if args.auto_approve else "draft review"
    print(f"Mode: {mode}")
    print("Type a message, or /help for commands.\n")

    while True:
        try:
            message = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye!")
            break

        if not message:
            continue
        if message.lower() in ("quit", "exit"):
            print("Bye!")
            break

        if message.startswith("/"):
            _handle_command(message, business_id, customer_id, args.url)
            continue

        payload = {"business_id": business_id, "customer_id": customer_id, "message": message}

        try:
            resp = httpx.post(f"{args.url}/chat", json=payload, timeout=120.0)
        except httpx.ConnectError:
            print(f"Error: cannot connect to backend at {args.url}. Is it running?")
            continue
        except httpx.TimeoutException:
            print("Error: request timed out.")
            continue

        if resp.status_code != 200:
            print(f"Error ({resp.status_code}): {resp.text}")
            continue

        data = resp.json()

        if args.auto_approve:
            print(f"\nAgent: {data['reply']}\n")
        else:
            result = _show_draft(data)
            if result:
                print(f"\nApproved reply: {result}\n")
            else:
                print("Draft rejected.\n")


if __name__ == "__main__":
    main()

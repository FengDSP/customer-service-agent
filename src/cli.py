#!/usr/bin/env python3
"""CLI for interacting with the customer service agent backend."""

import argparse
import sys

import httpx

DEFAULT_URL = "http://localhost:8000"


def _get(url: str, path: str) -> list | None:
    try:
        resp = httpx.get(f"{url}{path}", timeout=10.0)
        if resp.status_code == 200:
            return resp.json()
    except (httpx.ConnectError, httpx.TimeoutException):
        pass
    return None


def _list_businesses(url: str) -> list[dict]:
    data = _get(url, "/businesses")
    return data if data else []


def _list_customers(url: str, business_id: str) -> list[dict]:
    data = _get(url, f"/businesses/{business_id}/customers")
    return data if data else []


def _print_businesses(businesses: list[dict]):
    if not businesses:
        print("  No businesses found.")
        return
    for b in businesses:
        print(f"  {b['business_id']:<20} {b['name']}")


def _print_customers(customers: list[dict]):
    if not customers:
        print("  No customers found.")
        return
    for c in customers:
        print(f"  {c['customer_id']:<12} {c['name']}")


def _select_business(url: str) -> str:
    businesses = _list_businesses(url)
    if not businesses:
        print("Error: no businesses available. Is the backend running?")
        sys.exit(1)
    print("Available businesses:")
    for i, b in enumerate(businesses, 1):
        print(f"  {i}. {b['business_id']:<20} {b['name']}")
    while True:
        choice = input("\nSelect business (number or ID): ").strip()
        if not choice:
            continue
        # Try as number
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(businesses):
                return businesses[idx]["business_id"]
        except ValueError:
            pass
        # Try as ID
        for b in businesses:
            if b["business_id"] == choice:
                return choice
        print("  Invalid choice, try again.")


def _select_customer(url: str, business_id: str) -> str:
    customers = _list_customers(url, business_id)
    if customers:
        print(f"\nCustomers ({business_id}):")
        _print_customers(customers)
    return input("\nEnter customer ID: ").strip()


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


def _handle_command(cmd: str, url: str, business_id: str, customer_id: str) -> tuple[str, str]:
    """Handle in-session /commands. Returns (business_id, customer_id) which may change."""
    parts = cmd.split(maxsplit=1)
    command = parts[0].lower()

    if command == "/help":
        print("\nCommands:")
        print("  /help          Show this help")
        print("  /businesses    List available businesses")
        print("  /customers     List customers for current business")
        print("  /switch <id>   Switch to a different business")
        print("  /info          Show current session info")
        print("  /history       Show conversation history")
        print("  quit / exit    End session\n")

    elif command == "/businesses":
        businesses = _list_businesses(url)
        print("\nAvailable businesses:")
        _print_businesses(businesses)
        print()

    elif command == "/customers":
        customers = _list_customers(url, business_id)
        print(f"\nCustomers ({business_id}):")
        _print_customers(customers)
        print()

    elif command == "/switch":
        if len(parts) < 2:
            print("Usage: /switch <business_id>")
        else:
            new_id = parts[1].strip()
            businesses = _list_businesses(url)
            if any(b["business_id"] == new_id for b in businesses):
                business_id = new_id
                print(f"Switched to business: {business_id}\n")
            else:
                print(f"Business '{new_id}' not found.\n")

    elif command == "/info":
        print(f"\n  Business: {business_id}")
        print(f"  Customer: {customer_id}")
        print(f"  Backend:  {url}\n")

    elif command == "/history":
        # History is server-side; we can't show it directly from CLI
        print("  (History is stored server-side. Send a message to continue the conversation.)\n")

    else:
        print(f"  Unknown command: {command}. Type /help for available commands.\n")

    return business_id, customer_id


def main():
    parser = argparse.ArgumentParser(description="Customer service agent CLI")
    parser.add_argument("--business", help="Business ID to use")
    parser.add_argument("--customer", help="Customer ID")
    parser.add_argument("--url", default=DEFAULT_URL, help=f"Backend URL (default: {DEFAULT_URL})")
    parser.add_argument("--list-businesses", action="store_true", help="List available businesses")
    parser.add_argument("--list-customers", action="store_true", help="List customers for a business")
    parser.add_argument("--auto-approve", action="store_true", help="Skip draft review, print replies directly")
    args = parser.parse_args()

    # Handle list flags
    if args.list_businesses:
        businesses = _list_businesses(args.url)
        print("Available businesses:")
        _print_businesses(businesses)
        return

    if args.list_customers:
        if not args.business:
            print("Error: --business required with --list-customers")
            return
        customers = _list_customers(args.url, args.business)
        print(f"Customers ({args.business}):")
        _print_customers(customers)
        return

    # Interactive selection if args missing
    business_id = args.business
    if not business_id:
        business_id = _select_business(args.url)

    customer_id = args.customer
    if not customer_id:
        customer_id = _select_customer(args.url, business_id)
    if not customer_id:
        print("Error: customer ID is required.")
        return

    # Fetch business name for banner
    businesses = _list_businesses(args.url)
    biz_name = business_id
    for b in businesses:
        if b["business_id"] == business_id:
            biz_name = b["name"]
            break

    # Fetch customer name if available
    cust_display = customer_id
    customers = _list_customers(args.url, business_id)
    for c in customers:
        if c["customer_id"] == customer_id:
            cust_display = f"{customer_id} ({c['name']})"
            break

    # Startup banner
    print(f"\nConnected to {biz_name}")
    print(f"Customer: {cust_display}")
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

        # Handle /commands
        if message.startswith("/"):
            business_id, customer_id = _handle_command(
                message, args.url, business_id, customer_id
            )
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

#!/usr/bin/env python3
"""CLI for interacting with the customer service agent backend."""

import argparse
import json
import sys
import threading

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


def _handle_command(cmd: str, business_id: str, customer_id: str, url: str, cs_mode: bool):
    """Handle in-session /commands."""
    command = cmd.split()[0].lower()

    if command == "/help":
        print("\nCommands:")
        print("  /help       Show this help")
        print("  /info       Show current session info")
        print("  /history    Show conversation history")
        print("  quit        End session")
        if not cs_mode:
            print("\nIn customer mode: type a message and a CS agent will reply from the admin UI.")
        print()

    elif command == "/info":
        print(f"\n  Business: {business_id}")
        print(f"  Customer: {customer_id}")
        print(f"  Backend:  {url}")
        print(f"  Mode:     {'cs-agent' if cs_mode else 'customer'}\n")

    elif command == "/history":
        _show_history(url, business_id, customer_id)

    else:
        print(f"  Unknown command: {command}. Type /help for available commands.\n")


def _start_sse_listener(url: str, business_id: str, customer_id: str, stop_event: threading.Event):
    """Background thread that listens for SSE reply events and prints them."""
    sse_url = f"{url}/conversations/{business_id}/events"
    while not stop_event.is_set():
        try:
            with httpx.stream("GET", sse_url, timeout=None) as response:
                event_type = ""
                data_buf = ""
                for line in response.iter_lines():
                    if stop_event.is_set():
                        break
                    if line.startswith("event: "):
                        event_type = line[7:].strip()
                    elif line.startswith("data: "):
                        data_buf = line[6:]
                    elif line == "":
                        # End of event
                        if event_type == "reply" and data_buf:
                            try:
                                payload = json.loads(data_buf)
                                if payload.get("customer_id") == customer_id:
                                    reply = payload.get("reply", "")
                                    print(f"\nAgent: {reply}\n")
                                    # Re-show prompt hint
                                    sys.stdout.write("You: ")
                                    sys.stdout.flush()
                            except json.JSONDecodeError:
                                pass
                        event_type = ""
                        data_buf = ""
        except (httpx.ConnectError, httpx.RemoteProtocolError, httpx.ReadError):
            if stop_event.is_set():
                break
            # Reconnect after a brief pause
            stop_event.wait(2)
        except Exception:
            if stop_event.is_set():
                break
            stop_event.wait(2)


def main():
    parser = argparse.ArgumentParser(description="Customer service agent CLI")
    parser.add_argument("--business", help="Business ID to use")
    parser.add_argument("--customer", help="Customer ID")
    parser.add_argument("--url", default=DEFAULT_URL, help=f"Backend URL (default: {DEFAULT_URL})")
    parser.add_argument(
        "--list-businesses", action="store_true", help="List available businesses and exit"
    )
    parser.add_argument(
        "--cs-mode",
        action="store_true",
        help="CS agent mode: review/edit/approve AI-generated draft replies",
    )
    parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="(CS mode only) Skip draft review, print replies directly",
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

    if args.auto_approve and not args.cs_mode:
        parser.error("--auto-approve requires --cs-mode")

    business_id = args.business
    customer_id = args.customer
    cs_mode = args.cs_mode

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
    if cs_mode:
        mode = "auto-approve" if args.auto_approve else "draft review"
    else:
        mode = "customer"
    print(f"Mode: {mode}")
    if cs_mode:
        print("Type a message, or /help for commands.\n")
    else:
        print("\nType a message to start chatting. A CS agent will reply from the admin UI.")
        print("Type /help for commands.\n")

    # In customer mode, start SSE listener for reply events
    stop_event = threading.Event()
    sse_thread = None
    if not cs_mode:
        sse_thread = threading.Thread(
            target=_start_sse_listener,
            args=(args.url, business_id, customer_id, stop_event),
            daemon=True,
        )
        sse_thread.start()

    try:
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
                _handle_command(message, business_id, customer_id, args.url, cs_mode)
                continue

            payload = {"business_id": business_id, "customer_id": customer_id, "message": message}

            if not cs_mode:
                # Customer mode: send message, wait for reply via SSE
                try:
                    resp = httpx.post(f"{args.url}/messages", json=payload, timeout=10.0)
                except httpx.ConnectError:
                    print(f"Error: cannot connect to backend at {args.url}. Is it running?")
                    continue
                if resp.status_code != 200:
                    print(f"Error ({resp.status_code}): {resp.text}")
                else:
                    print("  (message sent, waiting for reply...)\n")
                continue

            # CS agent mode: send via /chat and review draft
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
    finally:
        stop_event.set()
        if sse_thread:
            sse_thread.join(timeout=3)


if __name__ == "__main__":
    main()

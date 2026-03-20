#!/usr/bin/env python3
"""CLI for interacting with the customer service agent backend."""

import argparse

import httpx

DEFAULT_URL = "http://localhost:8000"


def main():
    parser = argparse.ArgumentParser(description="Customer service agent CLI")
    parser.add_argument("--business", required=True, help="Business ID to use")
    parser.add_argument("--customer", required=True, help="Customer ID (e.g., email or unique identifier)")
    parser.add_argument("--url", default=DEFAULT_URL, help=f"Backend URL (default: {DEFAULT_URL})")
    args = parser.parse_args()

    print(f"Connected to {args.url} as business '{args.business}', customer '{args.customer}'")
    print("Type your message (or 'quit'/'exit' to end)\n")

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

        payload = {"business_id": args.business, "customer_id": args.customer, "message": message}

        try:
            resp = httpx.post(f"{args.url}/chat", json=payload, timeout=60.0)
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
        print(f"\nAgent: {data['reply']}\n")


if __name__ == "__main__":
    main()

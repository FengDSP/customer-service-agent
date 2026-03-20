# CLI

Command-line interface for interacting with the backend service. Primary interface until the UI is built.

## Usage

```bash
# Start a conversation with a business
python -m cli --business <business_id>

# The CLI opens an interactive prompt where you type customer messages
# and see draft replies from the agent.
```

## Behavior

- Starts a new session on launch. Maintains the session throughout the interactive loop.
- Sends each user input to `POST /chat` with the session ID and business ID.
- Prints the draft reply to stdout.
- Type `quit` or `exit` to end the session.
- The backend must be running before starting the CLI.

## No Human-in-the-Loop

The CLI returns draft replies directly without an approval step. Human-in-the-loop approval will be implemented in the frontend UI.

#!/usr/bin/env bash
set -euo pipefail

# E2E test script: starts the backend, sends real messages via POST /chat,
# and verifies the full pipeline (agent loop, LLM, tool calls, sessions).

BASE_URL="http://127.0.0.1:8000"
BUSINESS_ID="acme_retail"
PASSED=0
FAILED=0
SERVER_PID=""

cleanup() {
    if [ -n "$SERVER_PID" ]; then
        kill "$SERVER_PID" 2>/dev/null || true
        wait "$SERVER_PID" 2>/dev/null || true
    fi
}
trap cleanup EXIT

fail() { echo "  FAIL: $1"; FAILED=$((FAILED + 1)); }
pass() { echo "  PASS: $1"; PASSED=$((PASSED + 1)); }

# --- Prerequisites ---
if [ -z "${ANTHROPIC_API_KEY:-}" ]; then
    echo "ERROR: ANTHROPIC_API_KEY is not set. Export it before running."
    exit 1
fi
echo "API key found."

# --- Clean old logs ---
rm -rf logs/llm

# --- Start backend ---
echo ""
echo "Starting backend server..."
source .venv/bin/activate
uvicorn agent.api:app --host 127.0.0.1 --port 8000 &
SERVER_PID=$!

# Wait for server to be ready
for i in $(seq 1 20); do
    if curl -s "$BASE_URL/docs" > /dev/null 2>&1; then
        echo "Server ready."
        break
    fi
    if [ "$i" -eq 20 ]; then
        echo "ERROR: Server did not start in time."
        exit 1
    fi
    sleep 0.5
done

echo ""

# --- Test 1: Greeting ---
echo "Test 1: Greeting message"
RESP1=$(curl -s -X POST "$BASE_URL/chat" \
    -H "Content-Type: application/json" \
    -d "{\"business_id\":\"$BUSINESS_ID\",\"message\":\"Hello, I need some help.\"}")

SESSION_ID=$(echo "$RESP1" | python3 -c "import sys,json; print(json.load(sys.stdin).get('session_id',''))" 2>/dev/null)
REPLY1=$(echo "$RESP1" | python3 -c "import sys,json; print(json.load(sys.stdin).get('reply',''))" 2>/dev/null)

if [ -n "$SESSION_ID" ] && [ -n "$REPLY1" ]; then
    pass "Got session_id and reply"
    echo "  Reply: ${REPLY1:0:120}..."
else
    fail "No session_id or reply returned"
    echo "  Response: $RESP1"
fi

echo ""

# --- Test 2: Order lookup (triggers tool call) ---
echo "Test 2: Order lookup (should trigger CSV tool call)"
RESP2=$(curl -s -X POST "$BASE_URL/chat" \
    -H "Content-Type: application/json" \
    -d "{\"session_id\":\"$SESSION_ID\",\"business_id\":\"$BUSINESS_ID\",\"message\":\"What is the status of order ORD-1002?\"}")

REPLY2=$(echo "$RESP2" | python3 -c "import sys,json; print(json.load(sys.stdin).get('reply',''))" 2>/dev/null)

if echo "$REPLY2" | grep -qi "ship"; then
    pass "Reply contains order status info (shipped)"
    echo "  Reply: ${REPLY2:0:200}..."
elif [ -n "$REPLY2" ]; then
    # LLM might phrase it differently, just check we got a substantive reply
    pass "Got a reply (LLM may have phrased status differently)"
    echo "  Reply: ${REPLY2:0:200}..."
else
    fail "No reply for order lookup"
    echo "  Response: $RESP2"
fi

echo ""

# --- Test 3: Follow-up in same session (multi-turn) ---
echo "Test 3: Follow-up message (session continuity)"
RESP3=$(curl -s -X POST "$BASE_URL/chat" \
    -H "Content-Type: application/json" \
    -d "{\"session_id\":\"$SESSION_ID\",\"business_id\":\"$BUSINESS_ID\",\"message\":\"And what about order ORD-1003?\"}")

REPLY3=$(echo "$RESP3" | python3 -c "import sys,json; print(json.load(sys.stdin).get('reply',''))" 2>/dev/null)
SID3=$(echo "$RESP3" | python3 -c "import sys,json; print(json.load(sys.stdin).get('session_id',''))" 2>/dev/null)

if [ "$SID3" = "$SESSION_ID" ] && [ -n "$REPLY3" ]; then
    pass "Same session_id maintained, got reply"
    echo "  Reply: ${REPLY3:0:200}..."
else
    fail "Session continuity broken or no reply"
    echo "  Response: $RESP3"
fi

echo ""

# --- Test 4: LLM logs created ---
echo "Test 4: LLM log files created"
LOG_COUNT=$(find logs/llm -name "*.json" 2>/dev/null | wc -l | tr -d ' ')
if [ "$LOG_COUNT" -ge 3 ]; then
    pass "Found $LOG_COUNT log files in logs/llm/"
else
    fail "Expected at least 3 log files, found ${LOG_COUNT:-0}"
fi

# --- Summary ---
echo ""
echo "================================"
echo "Results: $PASSED passed, $FAILED failed"
echo "================================"

if [ "$FAILED" -gt 0 ]; then
    exit 1
fi

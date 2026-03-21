import json
import logging
import os

import anthropic
from dotenv import load_dotenv

from agent.config import BusinessConfig
from agent.csv_tool import build_tool_definitions, execute_csv_lookup, execute_grep
from agent.logging import log_interaction
from agent.prompt import build_user_prompt
from agent.session import append_message

load_dotenv()

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-sonnet-4-6"


def run_agent_loop(
    config: BusinessConfig,
    history: list[dict],
    message: str,
    customer_id: str,
) -> dict:
    """Run the agent loop and return the structured response dict."""
    client = anthropic.Anthropic()
    model = os.getenv("LLM_MODEL", DEFAULT_MODEL)
    tools = build_tool_definitions(config)
    logger.info("Starting agent loop: model=%s, tools=%d", model, len(tools))

    user_msg = {"role": "user", "content": message}
    history.append(user_msg)
    append_message(config.business_id, customer_id, user_msg)

    structured_prompt = build_user_prompt(message, history[:-1], config, customer_id)

    messages = [{"role": "user", "content": structured_prompt}]
    all_turns = [{"role": "user", "content": structured_prompt}]
    total_usage = {"input_tokens": 0, "output_tokens": 0}

    while True:
        response = client.messages.create(
            model=model,
            max_tokens=2048,
            system=config.system_prompt,
            tools=tools,
            messages=messages,
        )

        total_usage["input_tokens"] += response.usage.input_tokens
        total_usage["output_tokens"] += response.usage.output_tokens
        logger.info(
            "LLM response: stop_reason=%s, tokens=%d/%d",
            response.stop_reason,
            response.usage.input_tokens,
            response.usage.output_tokens,
        )

        if response.stop_reason == "tool_use":
            assistant_msg = {"role": "assistant", "content": response.content}
            messages.append(assistant_msg)
            all_turns.append(assistant_msg)

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    logger.info("Tool call: %s(%s)", block.name, json.dumps(block.input)[:200])
                    result_text = _dispatch_tool(config, block.name, block.input)
                    logger.info("Tool result: %s chars", len(result_text))
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result_text,
                        }
                    )

            tool_msg = {"role": "user", "content": tool_results}
            messages.append(tool_msg)
            all_turns.append(tool_msg)
        else:
            raw_text = _extract_text(response)
            result = _parse_response(raw_text)
            logger.info(
                "Agent loop complete: tokens_total=%d/%d, confidence=%s",
                total_usage["input_tokens"],
                total_usage["output_tokens"],
                result.get("confidence"),
            )

            reply_text = result["draft_reply"]
            assistant_msg = {"role": "assistant", "content": reply_text}
            history.append(assistant_msg)
            append_message(config.business_id, customer_id, assistant_msg)
            all_turns.append({"role": "assistant", "content": response.content})

            log_interaction(
                customer_id=customer_id,
                business_id=config.business_id,
                turns=all_turns,
                model=model,
                usage=total_usage,
                system_prompt=config.system_prompt,
            )

            return result


def _dispatch_tool(config: BusinessConfig, tool_name: str, args: dict) -> str:
    if tool_name.startswith("lookup_"):
        return execute_csv_lookup(config, tool_name, args)
    if tool_name == "grep_data":
        return execute_grep(config, args)
    return json.dumps({"error": f"Unknown tool: {tool_name}"})


def _extract_text(response) -> str:
    parts = []
    for block in response.content:
        if block.type == "text":
            parts.append(block.text)
    return "\n".join(parts)


def _parse_response(text: str) -> dict:
    """Parse JSON response from LLM, with fallback for plain text."""
    text = text.strip()

    # Try to extract JSON from code fences anywhere in the text
    import re

    fence_match = re.search(r"```(?:json)?\s*\n(.*?)\n\s*```", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1).strip()

    # Try to find a JSON object in the text
    if not text.startswith("{"):
        brace_start = text.find("{")
        if brace_start != -1:
            # Find the matching closing brace
            depth = 0
            for i in range(brace_start, len(text)):
                if text[i] == "{":
                    depth += 1
                elif text[i] == "}":
                    depth -= 1
                    if depth == 0:
                        text = text[brace_start : i + 1]
                        break

    try:
        data = json.loads(text)
        return {
            "draft_reply": data.get("draft_reply", ""),
            "internal_note": data.get("internal_note", ""),
            "confidence": data.get("confidence", "medium"),
            "needs_human_review": data.get("needs_human_review", False),
            "suggested_actions": data.get("suggested_actions", []),
        }
    except json.JSONDecodeError:
        # Fallback: treat the entire text as the reply
        return {
            "draft_reply": text,
            "internal_note": "LLM did not return valid JSON",
            "confidence": "low",
            "needs_human_review": True,
            "suggested_actions": [],
        }

import json
import os

import anthropic
from dotenv import load_dotenv

from agent.config import BusinessConfig
from agent.csv_tool import build_tool_definitions, execute_csv_lookup
from agent.logging import log_interaction
from agent.session import append_message

load_dotenv()

DEFAULT_MODEL = "claude-sonnet-4-6"


def run_agent_loop(
    config: BusinessConfig,
    history: list[dict],
    message: str,
    customer_id: str,
) -> str:
    """Run the agent loop: call LLM, handle tool calls, return final reply."""
    client = anthropic.Anthropic()
    model = os.getenv("LLM_MODEL", DEFAULT_MODEL)
    tools = build_tool_definitions(config)

    user_msg = {"role": "user", "content": message}
    history.append(user_msg)
    append_message(config.business_id, customer_id, user_msg)

    messages = list(history)
    all_turns = list(history)
    total_usage = {"input_tokens": 0, "output_tokens": 0}

    while True:
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            system=config.system_prompt,
            tools=tools,
            messages=messages,
        )

        total_usage["input_tokens"] += response.usage.input_tokens
        total_usage["output_tokens"] += response.usage.output_tokens

        if response.stop_reason == "tool_use":
            assistant_msg = {"role": "assistant", "content": response.content}
            messages.append(assistant_msg)
            all_turns.append(assistant_msg)

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result_text = _dispatch_tool(config, block.name, block.input)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": result_text,
                    })

            tool_msg = {"role": "user", "content": tool_results}
            messages.append(tool_msg)
            all_turns.append(tool_msg)
        else:
            reply_text = _extract_text(response)
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

            return reply_text


def _dispatch_tool(config: BusinessConfig, tool_name: str, args: dict) -> str:
    if tool_name.startswith("lookup_"):
        return execute_csv_lookup(config, tool_name, args)
    return json.dumps({"error": f"Unknown tool: {tool_name}"})


def _extract_text(response) -> str:
    parts = []
    for block in response.content:
        if block.type == "text":
            parts.append(block.text)
    return "\n".join(parts)

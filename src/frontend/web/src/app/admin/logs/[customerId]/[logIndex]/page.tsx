"use client";

import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

interface Turn {
  role: string;
  content: string | TurnBlock[];
}

interface TurnBlock {
  type: string;
  text?: string;
  id?: string;
  name?: string;
  input?: Record<string, unknown>;
  tool_use_id?: string;
  content?: string;
}

interface LlmCall {
  call_index: number;
  system: string;
  messages: Turn[];
  response: Turn;
  model: string;
}

interface LogEntryFull {
  index: number;
  timestamp: string;
  system_prompt: string;
  turns: Turn[];
  model: string;
  usage: { input_tokens: number; output_tokens: number };
  llm_calls: LlmCall[];
}

function TurnView({ turn }: { turn: Turn }) {
  const roleColors: Record<string, string> = {
    user: "bg-blue-50 border-blue-200",
    assistant: "bg-green-50 border-green-200",
  };
  const color = roleColors[turn.role] || "bg-gray-50 border-gray-200";

  return (
    <div className={`rounded border p-3 ${color}`}>
      <div className="mb-1 text-xs font-medium uppercase text-gray-500">{turn.role}</div>
      {typeof turn.content === "string" ? (
        <pre className="whitespace-pre-wrap text-sm">{turn.content}</pre>
      ) : (
        <div className="space-y-2">
          {turn.content.map((block, i) => (
            <BlockView key={i} block={block} />
          ))}
        </div>
      )}
    </div>
  );
}

function BlockView({ block }: { block: TurnBlock }) {
  const [expanded, setExpanded] = useState(false);

  if (block.type === "text") {
    return <pre className="whitespace-pre-wrap text-sm">{block.text}</pre>;
  }

  if (block.type === "tool_use") {
    return (
      <div className="rounded bg-orange-50 border border-orange-200 p-2">
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1 text-xs font-medium text-orange-700"
        >
          <span>{expanded ? "▼" : "▶"}</span>
          Tool: {block.name}
        </button>
        {expanded && (
          <pre className="mt-2 text-xs text-gray-700 overflow-auto max-h-60">
            {JSON.stringify(block.input, null, 2)}
          </pre>
        )}
      </div>
    );
  }

  if (block.type === "tool_result") {
    return (
      <div className="rounded bg-purple-50 border border-purple-200 p-2">
        <button
          onClick={() => setExpanded(!expanded)}
          className="flex items-center gap-1 text-xs font-medium text-purple-700"
        >
          <span>{expanded ? "▼" : "▶"}</span>
          Tool Result
        </button>
        {expanded && (
          <pre className="mt-2 text-xs text-gray-700 overflow-auto max-h-60">
            {typeof block.content === "string" ? block.content : JSON.stringify(block.content, null, 2)}
          </pre>
        )}
      </div>
    );
  }

  return <pre className="text-xs text-gray-500">{JSON.stringify(block, null, 2)}</pre>;
}

export default function LogEntryPage() {
  return <Suspense fallback={<p className="text-gray-500">Loading...</p>}><LogEntryContent /></Suspense>;
}

function LogEntryContent() {
  const params = useParams();
  const searchParams = useSearchParams();
  const customerId = params.customerId as string;
  const logIndex = parseInt(params.logIndex as string, 10);
  const biz = searchParams.get("biz") || "";
  const [entry, setEntry] = useState<LogEntryFull | null>(null);
  const [loading, setLoading] = useState(true);
  const [showSystemPrompt, setShowSystemPrompt] = useState(false);

  useEffect(() => {
    if (!biz) return;
    setLoading(true);
    fetch(`/api/admin/logs/${biz}/${customerId}/${logIndex}`)
      .then((r) => r.json())
      .then(setEntry)
      .catch(() => setEntry(null))
      .finally(() => setLoading(false));
  }, [biz, customerId, logIndex]);

  if (loading) return <p className="text-gray-500">Loading...</p>;
  if (!entry) return <p className="text-red-500">Log entry not found.</p>;

  return (
    <div className="max-w-4xl">
      {/* Breadcrumb */}
      <nav className="mb-4 text-sm text-gray-500">
        <Link href={`/admin/logs?biz=${biz}`} className="hover:underline">Sessions</Link>
        <span className="mx-1">/</span>
        <Link href={`/admin/logs/${customerId}?biz=${biz}`} className="hover:underline">{customerId}</Link>
        <span className="mx-1">/</span>
        <span className="text-gray-900">{new Date(entry.timestamp).toLocaleString()}</span>
      </nav>

      <h2 className="mb-2 text-xl font-semibold">LLM Calls</h2>
      <div className="mb-4 flex gap-4 text-sm text-gray-500">
        <span>Model: {entry.model}</span>
        <span>Tokens: {entry.usage.input_tokens}/{entry.usage.output_tokens}</span>
        <span>LLM calls: {entry.llm_calls.length}</span>
      </div>

      {/* System prompt */}
      <div className="mb-6">
        <button
          onClick={() => setShowSystemPrompt(!showSystemPrompt)}
          className="text-sm text-gray-500 hover:text-gray-700"
        >
          {showSystemPrompt ? "▼" : "▶"} System Prompt
        </button>
        {showSystemPrompt && (
          <pre className="mt-2 rounded border border-gray-200 bg-gray-50 p-3 text-sm whitespace-pre-wrap max-h-60 overflow-auto">
            {entry.system_prompt}
          </pre>
        )}
      </div>

      {/* Conversation turns grouped by LLM call */}
      <div className="space-y-6">
        {entry.llm_calls.map((call, i) => (
          <div key={i} className="rounded-lg border border-gray-200 p-4">
            <div className="mb-3 flex items-center justify-between">
              <h3 className="text-sm font-medium text-gray-700">
                LLM Call #{call.call_index + 1}
              </h3>
              <Link
                href={`/admin/logs/${customerId}/${logIndex}/replay?biz=${biz}&call=${call.call_index}`}
                className="rounded bg-blue-600 px-3 py-1 text-xs text-white hover:bg-blue-700"
              >
                Replay
              </Link>
            </div>

            <div className="space-y-2">
              {call.messages.map((turn, j) => (
                <TurnView key={j} turn={turn} />
              ))}
              <div className="border-t border-dashed border-gray-300 pt-2">
                <TurnView turn={call.response} />
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

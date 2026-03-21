"use client";

import { diffWords } from "diff";
import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

interface LlmCall {
  call_index: number;
  system: string;
  messages: Record<string, unknown>[];
  response: { role: string; content: string | Record<string, unknown>[] };
  model: string;
}

interface ReplayResult {
  original: { text: string };
  replayed: { text: string; usage: { input_tokens: number; output_tokens: number } };
}

function extractResponseText(response: LlmCall["response"]): string {
  if (typeof response.content === "string") return response.content;
  if (Array.isArray(response.content)) {
    return response.content
      .filter((b: Record<string, unknown>) => b.type === "text")
      .map((b: Record<string, unknown>) => b.text as string)
      .join("\n");
  }
  return JSON.stringify(response.content);
}

function DiffView({ original, replayed }: { original: string; replayed: string }) {
  const parts = diffWords(original, replayed);

  return (
    <div className="rounded border border-gray-200 bg-white p-4 text-sm whitespace-pre-wrap font-mono">
      {parts.map((part, i) => (
        <span
          key={i}
          className={
            part.added
              ? "bg-green-200 text-green-900"
              : part.removed
                ? "bg-red-200 text-red-900 line-through"
                : ""
          }
        >
          {part.value}
        </span>
      ))}
    </div>
  );
}

const MODELS = [
  "claude-opus-4-6",
  "claude-sonnet-4-6",
  "claude-haiku-4-5-20251001",
];

export default function ReplayPage() {
  return <Suspense fallback={<p className="text-gray-500">Loading...</p>}><ReplayContent /></Suspense>;
}

function ReplayContent() {
  const params = useParams();
  const searchParams = useSearchParams();
  const customerId = params.customerId as string;
  const logIndex = parseInt(params.logIndex as string, 10);
  const biz = searchParams.get("biz") || "";
  const callIndex = parseInt(searchParams.get("call") || "0", 10);

  const [call, setCall] = useState<LlmCall | null>(null);
  const [system, setSystem] = useState("");
  const [messagesJson, setMessagesJson] = useState("");
  const [model, setModel] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [result, setResult] = useState<ReplayResult | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!biz) return;
    setLoading(true);
    fetch(`/api/admin/logs/${biz}/${customerId}/${logIndex}`)
      .then((r) => r.json())
      .then((entry) => {
        const c = entry.llm_calls?.[callIndex];
        if (c) {
          setCall(c);
          setSystem(c.system);
          setMessagesJson(JSON.stringify(c.messages, null, 2));
          setModel(c.model);
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [biz, customerId, logIndex, callIndex]);

  async function handleReplay() {
    if (!call) return;
    setError("");
    setSending(true);
    setResult(null);

    let messages;
    try {
      messages = JSON.parse(messagesJson);
    } catch {
      setError("Invalid JSON in messages field.");
      setSending(false);
      return;
    }

    const originalText = extractResponseText(call.response);

    try {
      const resp = await fetch("/api/admin/replay", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          model,
          system,
          messages,
          tools: [],
          original_response_text: originalText,
        }),
      });

      if (!resp.ok) {
        const detail = await resp.text();
        setError(`Replay failed: ${detail}`);
      } else {
        setResult(await resp.json());
      }
    } catch (e) {
      setError(`Request failed: ${e}`);
    } finally {
      setSending(false);
    }
  }

  if (loading) return <p className="text-gray-500">Loading...</p>;
  if (!call) return <p className="text-red-500">LLM call not found.</p>;

  return (
    <div className="max-w-5xl">
      {/* Breadcrumb */}
      <nav className="mb-4 text-sm text-gray-500">
        <Link href={`/admin/logs?biz=${biz}`} className="hover:underline">Sessions</Link>
        <span className="mx-1">/</span>
        <Link href={`/admin/logs/${customerId}?biz=${biz}`} className="hover:underline">{customerId}</Link>
        <span className="mx-1">/</span>
        <Link href={`/admin/logs/${customerId}/${logIndex}?biz=${biz}`} className="hover:underline">Entry</Link>
        <span className="mx-1">/</span>
        <span className="text-gray-900">Replay Call #{callIndex + 1}</span>
      </nav>

      <h2 className="mb-4 text-xl font-semibold">Replay LLM Call</h2>

      {/* Model selector */}
      <div className="mb-4">
        <label className="mb-1 block text-sm font-medium text-gray-700">Model</label>
        <select
          value={model}
          onChange={(e) => setModel(e.target.value)}
          className="rounded border border-gray-300 px-3 py-1.5 text-sm"
        >
          {MODELS.map((m) => (
            <option key={m} value={m}>{m}</option>
          ))}
          {!MODELS.includes(model) && <option value={model}>{model}</option>}
        </select>
      </div>

      {/* System prompt */}
      <div className="mb-4">
        <label className="mb-1 block text-sm font-medium text-gray-700">System Prompt</label>
        <textarea
          value={system}
          onChange={(e) => setSystem(e.target.value)}
          rows={6}
          className="w-full rounded border border-gray-300 p-3 text-sm font-mono"
        />
      </div>

      {/* Messages */}
      <div className="mb-4">
        <label className="mb-1 block text-sm font-medium text-gray-700">Messages (JSON)</label>
        <textarea
          value={messagesJson}
          onChange={(e) => setMessagesJson(e.target.value)}
          rows={12}
          className="w-full rounded border border-gray-300 p-3 text-sm font-mono"
        />
      </div>

      {/* Send button */}
      <button
        onClick={handleReplay}
        disabled={sending}
        className="rounded bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
      >
        {sending ? "Sending..." : "Send Replay"}
      </button>

      {error && <p className="mt-4 text-red-600 text-sm">{error}</p>}

      {/* Results */}
      {result && (
        <div className="mt-6 space-y-4">
          <div className="flex gap-2 text-sm text-gray-500">
            <span>Replay tokens: {result.replayed.usage.input_tokens}/{result.replayed.usage.output_tokens}</span>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <h3 className="mb-2 text-sm font-medium text-gray-700">Original Response</h3>
              <pre className="rounded border border-gray-200 bg-gray-50 p-3 text-sm whitespace-pre-wrap max-h-96 overflow-auto">
                {result.original.text}
              </pre>
            </div>
            <div>
              <h3 className="mb-2 text-sm font-medium text-gray-700">Replayed Response</h3>
              <pre className="rounded border border-gray-200 bg-gray-50 p-3 text-sm whitespace-pre-wrap max-h-96 overflow-auto">
                {result.replayed.text}
              </pre>
            </div>
          </div>

          <div>
            <h3 className="mb-2 text-sm font-medium text-gray-700">Diff</h3>
            <DiffView original={result.original.text} replayed={result.replayed.text} />
          </div>
        </div>
      )}
    </div>
  );
}

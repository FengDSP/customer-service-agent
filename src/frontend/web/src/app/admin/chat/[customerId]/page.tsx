"use client";

import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useRef, useState } from "react";

interface Message {
  role: string;
  content: string;
  timestamp?: string;
}

interface DraftResult {
  reply: string;
  confidence: string;
  needs_human_review: boolean;
  internal_note: string;
  suggested_actions: string[];
}

interface ContextData {
  [source: string]: {
    columns: string[];
    rows: string[][];
  };
}

export default function ChatViewPage() {
  return (
    <Suspense fallback={<p className="text-gray-500">Loading...</p>}>
      <ChatView />
    </Suspense>
  );
}

function ChatView() {
  const params = useParams();
  const searchParams = useSearchParams();
  const biz = searchParams.get("biz") || "";
  const customerId = params.customerId as string;

  const [messages, setMessages] = useState<Message[]>([]);
  const [context, setContext] = useState<ContextData>({});
  const [draft, setDraft] = useState("");
  const [draftMeta, setDraftMeta] = useState<DraftResult | null>(null);
  const [generating, setGenerating] = useState(false);
  const [sending, setSending] = useState(false);
  const [loading, setLoading] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const fetchHistory = useCallback(() => {
    if (!biz || !customerId) return;
    fetch(`/api/history/${biz}/${customerId}`)
      .then((r) => r.json())
      .then((data) => {
        setMessages(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [biz, customerId]);

  const fetchContext = useCallback(() => {
    if (!biz || !customerId) return;
    fetch(`/api/conversations/${biz}/${customerId}/context`)
      .then((r) => r.json())
      .then(setContext)
      .catch(() => {});
  }, [biz, customerId]);

  useEffect(() => {
    fetchHistory();
    fetchContext();

    // SSE: listen for new customer messages
    if (!biz) return;
    const es = new EventSource(`/api/conversations/${biz}/events`);
    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.customer_id === customerId) {
          fetchHistory();
        }
      } catch {
        // ignore parse errors
      }
    };
    return () => es.close();
  }, [fetchHistory, fetchContext, biz, customerId]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const hasUnreplied = messages.length > 0 && messages[messages.length - 1].role === "user";

  const generateDraft = async () => {
    setGenerating(true);
    try {
      const resp = await fetch(`/api/conversations/${biz}/${customerId}/draft`, {
        method: "POST",
      });
      if (resp.ok) {
        const data: DraftResult = await resp.json();
        setDraft(data.reply);
        setDraftMeta(data);
        // Refresh history since agent loop may have added the reply
        fetchHistory();
      }
    } catch {
      // ignore
    } finally {
      setGenerating(false);
    }
  };

  const sendReply = async () => {
    if (!draft.trim()) return;
    setSending(true);
    try {
      const resp = await fetch(`/api/conversations/${biz}/${customerId}/send`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ reply: draft }),
      });
      if (resp.ok) {
        setDraft("");
        setDraftMeta(null);
        fetchHistory();
      }
    } catch {
      // ignore
    } finally {
      setSending(false);
    }
  };

  // Auto-generate draft when there's an unreplied message and no draft yet
  useEffect(() => {
    if (hasUnreplied && !draft && !generating && !loading) {
      generateDraft();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasUnreplied, loading]);

  if (!biz) return <p className="text-gray-500">Select a business above.</p>;

  return (
    <div className="flex h-full gap-4">
      {/* Main chat area */}
      <div className="flex flex-1 flex-col min-w-0">
        {/* Header */}
        <div className="mb-4 flex items-center gap-3">
          <Link
            href={`/admin/chat?biz=${biz}`}
            className="text-sm text-gray-500 hover:text-gray-700"
          >
            &larr; Back
          </Link>
          <h2 className="text-lg font-semibold">{decodeURIComponent(customerId)}</h2>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-auto rounded border border-gray-200 bg-white p-4">
          {loading ? (
            <p className="text-gray-500">Loading...</p>
          ) : messages.length === 0 ? (
            <p className="text-gray-500">No messages yet.</p>
          ) : (
            <div className="space-y-3">
              {messages.map((msg, i) => (
                <div
                  key={i}
                  className={`flex ${msg.role === "user" ? "justify-start" : "justify-end"}`}
                >
                  <div
                    className={`max-w-[75%] rounded-lg px-3 py-2 text-sm ${
                      msg.role === "user"
                        ? "bg-gray-100 text-gray-800"
                        : "bg-blue-500 text-white"
                    }`}
                  >
                    <p className="whitespace-pre-wrap">{msg.content}</p>
                    {msg.timestamp && (
                      <p
                        className={`mt-1 text-xs ${
                          msg.role === "user" ? "text-gray-400" : "text-blue-200"
                        }`}
                      >
                        {new Date(msg.timestamp).toLocaleString()}
                      </p>
                    )}
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Draft area */}
        <div className="mt-3 rounded border border-gray-200 bg-white p-3">
          {draftMeta && (
            <div className="mb-2 flex items-center gap-3 text-xs text-gray-500">
              <span>
                Confidence:{" "}
                <span
                  className={
                    draftMeta.confidence === "high"
                      ? "text-green-600"
                      : draftMeta.confidence === "low"
                        ? "text-red-600"
                        : "text-yellow-600"
                  }
                >
                  {draftMeta.confidence}
                </span>
              </span>
              {draftMeta.needs_human_review && (
                <span className="rounded bg-yellow-100 px-1.5 py-0.5 text-yellow-700">
                  Review required
                </span>
              )}
              {draftMeta.internal_note && (
                <span className="text-gray-400" title={draftMeta.internal_note}>
                  Note: {draftMeta.internal_note.slice(0, 60)}
                </span>
              )}
            </div>
          )}
          <textarea
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder={generating ? "Generating draft..." : "Draft reply..."}
            disabled={generating}
            rows={3}
            className="w-full resize-none rounded border border-gray-200 px-3 py-2 text-sm focus:border-blue-400 focus:outline-none disabled:bg-gray-50"
          />
          <div className="mt-2 flex items-center gap-2">
            <button
              onClick={sendReply}
              disabled={!draft.trim() || sending}
              className="rounded bg-blue-500 px-4 py-1.5 text-sm font-medium text-white hover:bg-blue-600 disabled:opacity-50"
            >
              {sending ? "Sending..." : "Send"}
            </button>
            {hasUnreplied && !generating && (
              <button
                onClick={generateDraft}
                className="rounded border border-gray-300 px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-50"
              >
                Regenerate Draft
              </button>
            )}
            {generating && (
              <span className="text-sm text-gray-400">Generating draft...</span>
            )}
          </div>
        </div>
      </div>

      {/* Right sidebar: customer context */}
      <div className="w-80 shrink-0 overflow-auto">
        <h3 className="mb-3 text-sm font-semibold text-gray-700">Customer Context</h3>
        {Object.keys(context).length === 0 ? (
          <p className="text-sm text-gray-400">No context configured.</p>
        ) : (
          <div className="space-y-4">
            {Object.entries(context).map(([source, data]) => (
              <div key={source} className="rounded border border-gray-200 bg-white">
                <div className="border-b border-gray-100 px-3 py-2">
                  <h4 className="text-xs font-semibold uppercase text-gray-500">{source}</h4>
                </div>
                {data.rows.length === 0 ? (
                  <p className="px-3 py-2 text-xs text-gray-400">No data found.</p>
                ) : (
                  <div className="max-h-64 overflow-auto">
                    <table className="w-full text-xs">
                      <thead>
                        <tr className="border-b border-gray-100">
                          {data.columns.map((col) => (
                            <th
                              key={col}
                              className="whitespace-nowrap px-2 py-1 text-left font-medium text-gray-500"
                            >
                              {col}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {data.rows.map((row, i) => (
                          <tr key={i} className="border-b border-gray-50">
                            {row.map((cell, j) => (
                              <td
                                key={j}
                                className="whitespace-nowrap px-2 py-1 text-gray-600"
                              >
                                {cell}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

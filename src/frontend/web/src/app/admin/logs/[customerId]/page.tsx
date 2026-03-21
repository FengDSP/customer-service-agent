"use client";

import Link from "next/link";
import { useParams, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

interface LogEntry {
  index: number;
  timestamp: string;
  customer_message: string;
  draft_reply: string;
  model: string;
  confidence: string;
  usage: { input_tokens: number; output_tokens: number };
  turns_count: number;
}

export default function CustomerLogsPage() {
  return <Suspense fallback={<p className="text-gray-500">Loading...</p>}><CustomerLogsContent /></Suspense>;
}

function CustomerLogsContent() {
  const params = useParams();
  const searchParams = useSearchParams();
  const customerId = params.customerId as string;
  const biz = searchParams.get("biz") || "";
  const [entries, setEntries] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!biz || !customerId) return;
    setLoading(true);
    fetch(`/api/admin/logs/${biz}/${customerId}`)
      .then((r) => r.json())
      .then(setEntries)
      .catch(() => setEntries([]))
      .finally(() => setLoading(false));
  }, [biz, customerId]);

  if (loading) return <p className="text-gray-500">Loading...</p>;

  return (
    <div>
      {/* Breadcrumb */}
      <nav className="mb-4 text-sm text-gray-500">
        <Link href={`/admin/logs?biz=${biz}`} className="hover:underline">
          Sessions
        </Link>
        <span className="mx-1">/</span>
        <span className="text-gray-900">{customerId}</span>
      </nav>

      <h2 className="mb-4 text-xl font-semibold">Draft Replies — {customerId}</h2>

      {entries.length === 0 ? (
        <p className="text-gray-500">No log entries found.</p>
      ) : (
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-gray-200 text-gray-500">
              <th className="py-2 pr-4 font-medium">Timestamp</th>
              <th className="py-2 pr-4 font-medium">Customer Message</th>
              <th className="py-2 pr-4 font-medium">Draft Reply</th>
              <th className="py-2 pr-4 font-medium">Model</th>
              <th className="py-2 pr-4 font-medium">Confidence</th>
              <th className="py-2 pr-4 font-medium">Tokens</th>
              <th className="py-2 pr-4 font-medium">Turns</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((e) => (
              <tr key={e.index} className="border-b border-gray-100 hover:bg-gray-50">
                <td className="py-2 pr-4 text-gray-600 whitespace-nowrap">
                  <Link
                    href={`/admin/logs/${customerId}/${e.index}?biz=${biz}`}
                    className="text-blue-600 hover:underline"
                  >
                    {new Date(e.timestamp).toLocaleString()}
                  </Link>
                </td>
                <td className="py-2 pr-4 max-w-xs truncate" title={e.customer_message}>
                  {e.customer_message}
                </td>
                <td className="py-2 pr-4 max-w-xs truncate" title={e.draft_reply}>
                  {e.draft_reply}
                </td>
                <td className="py-2 pr-4 text-gray-600 text-xs">{e.model}</td>
                <td className="py-2 pr-4">
                  <span
                    className={`rounded px-2 py-0.5 text-xs ${
                      e.confidence === "high"
                        ? "bg-green-100 text-green-700"
                        : e.confidence === "medium"
                          ? "bg-yellow-100 text-yellow-700"
                          : "bg-red-100 text-red-700"
                    }`}
                  >
                    {e.confidence}
                  </span>
                </td>
                <td className="py-2 pr-4 text-gray-600 text-xs">
                  {e.usage.input_tokens}/{e.usage.output_tokens}
                </td>
                <td className="py-2 pr-4">{e.turns_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

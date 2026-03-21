"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useCallback, useEffect, useState } from "react";

interface Conversation {
  customer_id: string;
  name: string;
  last_message: string;
  last_timestamp: string;
  has_unreplied: boolean;
}

export default function ChatPage() {
  return (
    <Suspense fallback={<p className="text-gray-500">Loading...</p>}>
      <ChatContent />
    </Suspense>
  );
}

function ChatContent() {
  const searchParams = useSearchParams();
  const biz = searchParams.get("biz") || "";
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(() => {
    if (!biz) return;
    fetch(`/api/conversations/${biz}/pending`)
      .then((r) => r.json())
      .then(setConversations)
      .catch(() => setConversations([]))
      .finally(() => setLoading(false));
  }, [biz]);

  useEffect(() => {
    setLoading(true);
    refresh();
    const interval = setInterval(refresh, 5000);
    return () => clearInterval(interval);
  }, [refresh]);

  if (!biz) return <p className="text-gray-500">Select a business above.</p>;
  if (loading) return <p className="text-gray-500">Loading...</p>;

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-xl font-semibold">Customer Conversations</h2>
        <button
          onClick={refresh}
          className="rounded border border-gray-300 px-3 py-1.5 text-sm text-gray-600 hover:bg-gray-50"
        >
          Refresh
        </button>
      </div>
      {conversations.length === 0 ? (
        <p className="text-gray-500">No conversations yet.</p>
      ) : (
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-gray-200 text-gray-500">
              <th className="py-2 pr-4 font-medium w-8"></th>
              <th className="py-2 pr-4 font-medium">Customer</th>
              <th className="py-2 pr-4 font-medium">Last Message</th>
              <th className="py-2 pr-4 font-medium">Time</th>
            </tr>
          </thead>
          <tbody>
            {conversations.map((c) => (
              <tr
                key={c.customer_id}
                className={`border-b border-gray-100 hover:bg-gray-50 ${
                  c.has_unreplied ? "bg-blue-50/50" : ""
                }`}
              >
                <td className="py-2 pr-2 text-center">
                  {c.has_unreplied && (
                    <span className="inline-block h-2.5 w-2.5 rounded-full bg-blue-500" title="Unreplied" />
                  )}
                </td>
                <td className="py-2 pr-4">
                  <Link
                    href={`/admin/chat/${c.customer_id}?biz=${biz}`}
                    className="text-blue-600 hover:underline"
                  >
                    {c.name}
                  </Link>
                  <span className="ml-2 text-xs text-gray-400">{c.customer_id}</span>
                </td>
                <td className="py-2 pr-4 text-gray-600 max-w-xs truncate">
                  {c.last_message}
                </td>
                <td className="py-2 pr-4 text-gray-500 whitespace-nowrap">
                  {c.last_timestamp ? new Date(c.last_timestamp).toLocaleString() : ""}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

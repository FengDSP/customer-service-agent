"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

interface CustomerLog {
  customer_id: string;
  last_interaction: string;
  total_interactions: number;
  total_tokens: { input: number; output: number };
}

export default function LogsPage() {
  return <Suspense fallback={<p className="text-gray-500">Loading...</p>}><LogsContent /></Suspense>;
}

function LogsContent() {
  const searchParams = useSearchParams();
  const biz = searchParams.get("biz") || "";
  const [customers, setCustomers] = useState<CustomerLog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!biz) return;
    setLoading(true);
    fetch(`/api/admin/logs/${biz}/customers`)
      .then((r) => r.json())
      .then(setCustomers)
      .catch(() => setCustomers([]))
      .finally(() => setLoading(false));
  }, [biz]);

  if (!biz) return <p className="text-gray-500">Select a business above.</p>;
  if (loading) return <p className="text-gray-500">Loading...</p>;

  return (
    <div>
      <h2 className="mb-4 text-xl font-semibold">Customer Sessions</h2>
      {customers.length === 0 ? (
        <p className="text-gray-500">No log files found for this business.</p>
      ) : (
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="border-b border-gray-200 text-gray-500">
              <th className="py-2 pr-4 font-medium">Customer ID</th>
              <th className="py-2 pr-4 font-medium">Last Interaction</th>
              <th className="py-2 pr-4 font-medium">Total Interactions</th>
              <th className="py-2 pr-4 font-medium">Tokens (in/out)</th>
            </tr>
          </thead>
          <tbody>
            {customers.map((c) => (
              <tr key={c.customer_id} className="border-b border-gray-100 hover:bg-gray-50">
                <td className="py-2 pr-4">
                  <Link
                    href={`/admin/logs/${c.customer_id}?biz=${biz}`}
                    className="text-blue-600 hover:underline"
                  >
                    {c.customer_id}
                  </Link>
                </td>
                <td className="py-2 pr-4 text-gray-600">
                  {new Date(c.last_interaction).toLocaleString()}
                </td>
                <td className="py-2 pr-4">{c.total_interactions}</td>
                <td className="py-2 pr-4 text-gray-600">
                  {c.total_tokens.input.toLocaleString()} / {c.total_tokens.output.toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

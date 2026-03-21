"use client";

import Link from "next/link";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

interface Business {
  business_id: string;
  name: string;
}

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return <Suspense fallback={<p className="text-gray-500">Loading...</p>}><AdminLayoutInner>{children}</AdminLayoutInner></Suspense>;
}

function AdminLayoutInner({ children }: { children: React.ReactNode }) {
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [selectedBiz, setSelectedBiz] = useState(searchParams.get("biz") || "");
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const router = useRouter();

  useEffect(() => {
    fetch("/api/businesses")
      .then((r) => r.json())
      .then((data) => {
        setBusinesses(data);
        const fromUrl = searchParams.get("biz");
        if (fromUrl) {
          setSelectedBiz(fromUrl);
        } else if (data.length > 0) {
          setSelectedBiz(data[0].business_id);
        }
      })
      .catch(() => {});
  }, [searchParams]);

  function handleBizChange(e: React.ChangeEvent<HTMLSelectElement>) {
    const biz = e.target.value;
    setSelectedBiz(biz);
    router.push(`/admin/logs?biz=${biz}`);
  }

  return (
    <div className="flex h-screen flex-col">
      {/* Top bar */}
      <header className="flex h-14 items-center border-b border-gray-200 bg-white px-4 gap-4">
        <h1 className="text-lg font-semibold">CS Admin</h1>
        <select
          value={selectedBiz}
          onChange={handleBizChange}
          className="rounded border border-gray-300 px-3 py-1.5 text-sm"
        >
          {businesses.map((b) => (
            <option key={b.business_id} value={b.business_id}>
              {b.name}
            </option>
          ))}
        </select>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Left nav */}
        <nav className="w-52 border-r border-gray-200 bg-white p-4">
          <ul className="space-y-1">
            <li>
              <Link
                href={`/admin/logs?biz=${selectedBiz}`}
                className={`block rounded px-3 py-2 text-sm ${
                  pathname.startsWith("/admin/logs")
                    ? "bg-blue-50 font-medium text-blue-700"
                    : "text-gray-700 hover:bg-gray-100"
                }`}
              >
                LLM Log Viewer
              </Link>
            </li>
          </ul>
        </nav>

        {/* Main content */}
        <main className="flex-1 overflow-auto p-6">{children}</main>
      </div>
    </div>
  );
}

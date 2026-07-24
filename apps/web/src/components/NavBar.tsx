"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

// Two-sided nav: the demo is one system with two doors. Prior auth is a
// step inside the doctor flow (see FlowStrip), not a top-level destination.
const LINKS = [
  { href: "/intake", label: "Patient", activeOn: ["/intake"] },
  { href: "/worklist", label: "Doctor", activeOn: ["/worklist", "/pa-packets", "/dashboard"] },
];

export default function NavBar() {
  const pathname = usePathname();

  return (
    <header className="sticky top-[33px] z-40 w-full border-b border-slate-200 bg-white/95 backdrop-blur dark:border-slate-800 dark:bg-slate-950/95">
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6">
        <Link href="/" className="flex items-baseline gap-2">
          <span className="text-lg font-bold tracking-tight text-slate-900 dark:text-white">
            Meridian
          </span>
          <span className="hidden text-xs font-medium text-slate-400 sm:inline">
            the end of &ldquo;please hold&rdquo;
          </span>
        </Link>
        <ul className="flex items-center gap-1">
          {LINKS.map((link) => {
            const active = link.activeOn.some((p) => pathname?.startsWith(p));
            return (
              <li key={link.href}>
                <Link
                  href={link.href}
                  className={`rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                    active
                      ? "bg-slate-900 text-white dark:bg-white dark:text-slate-900"
                      : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
                  }`}
                >
                  {link.label}
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>
    </header>
  );
}

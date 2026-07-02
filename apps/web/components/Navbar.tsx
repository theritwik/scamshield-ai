"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useLang } from "@/lib/i18n";

const links = [
  { href: "/analyze", label: "Analyze", label_hi: "विश्लेषण" },
  { href: "/simulate", label: "Live Demo", label_hi: "लाइव डेमो" },
  { href: "/cases", label: "Cases", label_hi: "केस" },
  { href: "/investigator", label: "Command Centre", label_hi: "कमांड सेंटर" },
  { href: "/about", label: "About", label_hi: "परिचय" },
];

export function Navbar() {
  const path = usePathname();
  const { lang, setLang } = useLang();
  return (
    <header className="sticky top-0 z-40 border-b border-navy-800 bg-navy-950/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-2 px-4 py-3">
        <Link href="/" className="flex items-center gap-2 font-bold tracking-tight">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-accent-500 text-sm text-white">
            SS
          </span>
          <span className="hidden sm:inline">
            ScamShield <span className="text-accent-400">AI</span>
          </span>
        </Link>
        <nav className="flex items-center gap-1 overflow-x-auto text-sm">
          {links.map((l) => (
            <Link
              key={l.href}
              href={l.href}
              className={`whitespace-nowrap rounded-md px-3 py-1.5 transition-colors ${
                path?.startsWith(l.href)
                  ? "bg-navy-800 text-white"
                  : "text-ink-300 hover:text-white"
              }`}
            >
              {lang === "hi" ? l.label_hi : l.label}
            </Link>
          ))}
        </nav>
        <button
          onClick={() => setLang(lang === "en" ? "hi" : "en")}
          className="rounded-md border border-navy-600 px-2.5 py-1 text-xs font-semibold text-ink-300 hover:border-accent-400 hover:text-white"
          aria-label="Toggle language"
        >
          {lang === "en" ? "हिंदी" : "EN"}
        </button>
      </div>
    </header>
  );
}

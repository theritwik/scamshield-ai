import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { LangProvider } from "@/lib/i18n";
import { Navbar } from "@/components/Navbar";
import { ToastProvider } from "@/components/Toast";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "ScamShield AI — Digital Arrest Scam Defence",
  description:
    "Detect coercion. Interrupt fraud. Protect before payment. AI-powered digital-arrest scam defence and fraud intelligence for India (hackathon prototype).",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="font-sans min-h-screen antialiased">
        <LangProvider>
          <ToastProvider>
            <Navbar />
            <main className="mx-auto max-w-6xl px-4 pb-16 pt-6">{children}</main>
            <footer className="border-t border-navy-800 py-6 text-center text-xs text-ink-500">
              ScamShield AI — hackathon prototype. Simulated integrations. Synthetic data only.
              Decision support, not legal confirmation.
            </footer>
          </ToastProvider>
        </LangProvider>
      </body>
    </html>
  );
}

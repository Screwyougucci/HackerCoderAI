import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "HackerCoderAI Remote",
  description: "Cloud AI agent and isolated Vercel Sandbox runner",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}

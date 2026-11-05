import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Qill | Distributed Intelligence",
  description: "Eight-worker zero-cost distributed research control center",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}

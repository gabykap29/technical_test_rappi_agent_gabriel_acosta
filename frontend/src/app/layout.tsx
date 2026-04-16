import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Rappi Operations Intelligence",
  description: "LLM-powered operations analytics for Rappi technical case.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

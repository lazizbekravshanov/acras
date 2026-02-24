import type { Metadata } from "next";
import "@/styles/globals.css";
import DashboardShell from "@/components/layout/DashboardShell";

export const metadata: Metadata = {
  title: "ACRAS Dashboard",
  description:
    "AI Crash Report Automation System - Real-time traffic incident monitoring",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#0a0a0f] text-gray-100 antialiased">
        <DashboardShell>{children}</DashboardShell>
      </body>
    </html>
  );
}

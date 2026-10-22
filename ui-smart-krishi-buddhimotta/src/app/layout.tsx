import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "ক্ষেতসাথী | কৃষি বুদ্ধিমত্তা",
  description: "বাংলাদেশের কৃষকদের জন্য আবহাওয়া, ফসল পরিচর্যা ও AI কৃষি সহায়তা।",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="bn">
      <body>{children}</body>
    </html>
  );
}

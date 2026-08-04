import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin", "latin-ext"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "HolidaysHunter — Smart Travel Platform",
  description: "Automatyczny monitor i wyszukiwarka najatrakcyjniejszych ofert wakacyjnych",
  manifest: "/manifest.json",
  icons: {
    icon: "/icon.svg",
    apple: "/icon.svg",
  },
};

export const viewport: Viewport = {
  themeColor: "#0b0f19",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pl" suppressHydrationWarning className={`${inter.variable} h-full antialiased dark`}>
      <body suppressHydrationWarning className="min-h-full flex flex-col bg-[#0b0f19] text-slate-100 selection:bg-indigo-500 selection:text-white font-sans">
        {children}
      </body>
    </html>
  );
}

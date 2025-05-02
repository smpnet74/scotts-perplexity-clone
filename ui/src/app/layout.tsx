import type { Metadata } from "next";
import localFont from "next/font/local";
import { SpeedInsights } from "@vercel/speed-insights/next";
import { Analytics } from "@vercel/analytics/react";
import "@copilotkit/react-ui/styles.css";
import "./globals.css";
import { PangeaAuthProvider } from "@/lib/pangea-auth-provider";

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});
const geistMono = localFont({
  src: "./fonts/GeistMonoVF.woff",
  variable: "--font-geist-mono",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: "Scott's Perplexity Clone",
  description: "Scott's Perplexity Clone - An AI-powered research assistant inspired by Perplexity.ai.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <PangeaAuthProvider>
          {children}
        </PangeaAuthProvider>
        <SpeedInsights />
        <Analytics />
      </body>
    </html>
  );
}

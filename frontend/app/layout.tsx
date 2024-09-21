import type { Metadata } from "next";
import "./globals.css";
import { CSPostHogProvider } from './providers';

export const metadata: Metadata = {
  title: "Roborail Assistant",
  description: "Ai Assistant for Roborail",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <CSPostHogProvider>
        <body>{children}</body>
      </CSPostHogProvider>
    </html>
  );
}

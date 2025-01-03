import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Roborail Assistant",
  description: "Ai Assistant for Roborail",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <link rel="icon" href="icon.ico" />
      <link rel="icon" href="static/icon.ico" />
      <body>{children}</body>
    </html>
  );
}

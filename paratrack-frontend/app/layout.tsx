// app/layout.tsx
import type { Metadata } from "next";
import "./globals.css";
import ChatWidget from "@/components/ChatWidget";

export const metadata: Metadata = {
  title: "ParaTrack - Comparateur de prix parapharmacie Tunisie",
  description: "Comparez les prix des produits de parapharmacie en Tunisie",
  keywords: "parapharmacie, comparaison prix, Tunisie, produits beauté, soins",
  authors: [{ name: "ParaTrack" }],
  viewport: "width=device-width, initial-scale=1, maximum-scale=1",
  themeColor: "#2b5ef0",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="fr">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body>
        {children}
        <ChatWidget />
      </body>
    </html>
  );
}
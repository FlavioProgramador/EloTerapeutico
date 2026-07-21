import type { Metadata } from "next";
import { IBM_Plex_Mono, Outfit, Piazzolla, Work_Sans } from "next/font/google";

import { Providers } from "@/providers/providers";
import "./globals.css";
import "./orange-theme.css";
import "./legacy-typography.css";

const outfit = Outfit({
  subsets: ["latin"],
  variable: "--font-outfit",
  weight: ["300", "400", "500", "600", "700", "800"],
});

const piazzolla = Piazzolla({
  subsets: ["latin"],
  variable: "--font-display",
  weight: ["600", "700"],
});

const workSans = Work_Sans({
  subsets: ["latin"],
  variable: "--font-body",
  weight: ["400", "500", "700"],
});

const ibmPlexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  weight: ["400"],
});

export const metadata: Metadata = {
  title: "Elo Terapêutico – Prontuário Eletrônico & Gestão de Clínicas",
  description:
    "Plataforma de alta performance para psicólogos e terapeutas. Gestão de pacientes, prontuários criptografados em conformidade com a LGPD, agenda e controle financeiro completo.",
  keywords: [
    "psicologia",
    "terapia",
    "prontuário eletrônico",
    "gestão clínica",
    "LGPD",
    "agenda terapêutica",
  ],
  authors: [{ name: "Elo Terapêutico" }],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="pt-BR"
      className={`${outfit.variable} ${piazzolla.variable} ${workSans.variable} ${ibmPlexMono.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <body
        className="flex min-h-full flex-col font-sans"
        suppressHydrationWarning
      >
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}

import type { Metadata } from "next";
import { Outfit } from "next/font/google";
import { Providers } from "@/providers/providers";
import "./globals.css";

const outfit = Outfit({
  subsets: ["latin"],
  variable: "--font-outfit",
  weight: ["300", "400", "500", "600", "700", "800"],
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
      className={`${outfit.variable} h-full antialiased`}
      suppressHydrationWarning
    >
      <body className="min-h-full flex flex-col font-sans">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}


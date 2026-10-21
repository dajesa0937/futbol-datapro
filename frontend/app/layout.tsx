import type { Metadata, Viewport } from "next";
import "./globals.css";
import Shell from "@/components/Shell";

export const metadata: Metadata = {
  title: "Fútbol DataPro — Análisis del fútbol colombiano",
  description: "Estadísticas de los últimos 20 partidos y estimaciones probabilísticas, con la fuente y la cobertura de los datos siempre a la vista.",
  manifest: "/manifest.webmanifest",
  icons: { icon: "/icons/icon-192.png", apple: "/icons/icon-192.png" },
};
export const viewport: Viewport = { themeColor: "#0a1226", width: "device-width", initialScale: 1 };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es-CO" data-theme="dark" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: `try{var t=localStorage.getItem("datapro.theme");if(t==="light"||t==="dark")document.documentElement.setAttribute("data-theme",t)}catch(e){}` }} />
      </head>
      <body><Shell>{children}</Shell></body>
    </html>
  );
}

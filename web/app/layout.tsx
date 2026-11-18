import type { Metadata } from "next";
import "./globals.css";
import Header from "@/components/Header";
import { I18nProvider } from "@/lib/i18n";

export const metadata: Metadata = { title: "Jyotish Lab", description: "Vedic astrology – kundli, dasha, reports, remedies" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <I18nProvider>
          <Header />
          {children}
        </I18nProvider>
      </body>
    </html>
  );
}

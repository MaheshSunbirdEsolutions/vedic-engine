import Header from "@/components/Header";
import { I18nProvider } from "@/lib/i18n";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <I18nProvider>
      <Header />
      {children}
    </I18nProvider>
  );
}

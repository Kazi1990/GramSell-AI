import "./globals.css";

export const metadata = {
  title: "GramSell AI",
  description: "AI-powered business intelligence for rural sellers"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

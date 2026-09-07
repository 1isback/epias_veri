import './globals.css';
import Providers from './providers';

export const metadata = {
  title: 'EPİAŞ Data Platform',
  description: 'Enterprise Data Platform Architecture',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="tr">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}

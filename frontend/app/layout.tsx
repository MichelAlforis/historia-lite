import type { Metadata } from 'next'
import 'leaflet/dist/leaflet.css'
import './globals.css'

export const metadata: Metadata = {
  title: 'Historia Lite - Simulateur Geopolitique',
  description: 'Simulateur geopolitique moderne en version light',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="fr">
      <body className="font-sans">{children}</body>
    </html>
  )
}

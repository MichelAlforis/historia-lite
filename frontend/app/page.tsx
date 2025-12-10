import ClientPage from './ClientPage';

// Force dynamic rendering - skip static generation during build
export const dynamic = 'force-dynamic';

export default function HomePage() {
  return <ClientPage />;
}

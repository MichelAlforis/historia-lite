import { redirect } from 'next/navigation';

// Redirect root to /pax - the main player interface
export default function HomePage() {
  redirect('/pax');
}

'use client';

import dynamic from 'next/dynamic';

// Import GameApp dynamically with SSR disabled to avoid Zustand hydration issues
const GameApp = dynamic(() => import('@/components/GameApp'), {
  ssr: false,
  loading: () => (
    <div className="min-h-screen flex items-center justify-center bg-gray-900">
      <div className="text-center space-y-4">
        <div className="text-6xl animate-pulse">{'🌍'}</div>
        <div className="text-2xl font-bold text-white">Historia Lite - Debug Mode</div>
        <div className="text-gray-400">Chargement du monde...</div>
        <div className="w-48 h-2 bg-gray-700 rounded-full overflow-hidden mx-auto">
          <div className="h-full bg-blue-500 rounded-full animate-pulse" style={{ width: '60%' }} />
        </div>
      </div>
    </div>
  ),
});

export default function DebugPage() {
  return <GameApp />;
}

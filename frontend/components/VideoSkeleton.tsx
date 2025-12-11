'use client';

interface VideoSkeletonProps {
  message?: string;
  variant?: 'globe' | 'loop' | 'minimalist';
}

const VIDEO_SOURCES = {
  globe: '/video/geopolitical-globe.mp4',
  loop: '/video/nice-loop.mp4',
  minimalist: '/video/minimalist-world.mp4',
};

export default function VideoSkeleton({
  message = 'Chargement...',
  variant = 'minimalist'
}: VideoSkeletonProps) {
  return (
    <div className="min-h-screen bg-stone-900 flex flex-col items-center justify-center relative overflow-hidden">
      {/* Video background */}
      <div className="absolute inset-0 z-0">
        <video
          autoPlay
          loop
          muted
          playsInline
          className="w-full h-full object-cover opacity-60"
        >
          <source src={VIDEO_SOURCES[variant]} type="video/mp4" />
        </video>
        {/* Gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-stone-900 via-stone-900/50 to-transparent" />
      </div>

      {/* Content */}
      <div className="relative z-10 text-center">
        {/* Loading spinner */}
        <div className="mb-6">
          <div className="w-12 h-12 border-3 border-amber-400/30 border-t-amber-400 rounded-full animate-spin mx-auto" />
        </div>

        {/* Message */}
        <p className="text-xl text-stone-200 font-light tracking-wide">
          {message}
        </p>

        {/* Subtle animated dots */}
        <div className="flex justify-center gap-1 mt-4">
          <span className="w-1.5 h-1.5 bg-amber-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
          <span className="w-1.5 h-1.5 bg-amber-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
          <span className="w-1.5 h-1.5 bg-amber-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
        </div>
      </div>
    </div>
  );
}

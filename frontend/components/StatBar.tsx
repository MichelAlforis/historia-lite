'use client';

interface StatBarProps {
  label: string;
  value: number;
  maxValue?: number;
  color?: string;
  showValue?: boolean;
}

export function StatBar({
  label,
  value,
  maxValue = 100,
  color = 'bg-blue-500',
  showValue = true,
}: StatBarProps) {
  const percentage = Math.min(100, (value / maxValue) * 100);

  // Color based on value if not specified
  const barColor = color === 'auto'
    ? value >= 70 ? 'bg-green-500'
      : value >= 40 ? 'bg-yellow-500'
      : 'bg-red-500'
    : color;

  return (
    <div className="flex items-center gap-2 text-sm">
      <span className="w-24 text-gray-400 truncate">{label}</span>
      <div className="flex-1 h-2 bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`stat-bar h-full ${barColor} rounded-full`}
          style={{ width: `${percentage}%` }}
        />
      </div>
      {showValue && (
        <span className="w-8 text-right text-gray-300">{value}</span>
      )}
    </div>
  );
}

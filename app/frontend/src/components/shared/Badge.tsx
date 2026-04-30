interface BadgeProps {
  label: string
  color?: 'orange' | 'green' | 'blue' | 'yellow' | 'red' | 'gray'
}

const colorClasses = {
  orange: 'bg-orange-500/20 text-orange-400',
  green: 'bg-green-500/20 text-green-400',
  blue: 'bg-blue-500/20 text-blue-400',
  yellow: 'bg-yellow-500/20 text-yellow-400',
  red: 'bg-red-500/20 text-red-400',
  gray: 'bg-gray-700 text-gray-400',
}

export function Badge({ label, color = 'gray' }: BadgeProps) {
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${colorClasses[color]}`}>
      {label}
    </span>
  )
}

interface CameraFeedProps {
  streamUrl: string
  className?: string
}

export function CameraFeed({ streamUrl, className = '' }: CameraFeedProps) {
  if (!streamUrl) {
    return (
      <div className={`bg-gray-900 flex items-center justify-center ${className}`}>
        <p className="text-gray-500 text-sm">Camera not connected</p>
      </div>
    )
  }
  return (
    <img
      src={streamUrl}
      alt="Live camera feed"
      className={`object-cover w-full h-full ${className}`}
      onError={(e) => {
        // Retry stream on error after short delay
        const img = e.currentTarget
        setTimeout(() => { img.src = streamUrl }, 2000)
      }}
    />
  )
}

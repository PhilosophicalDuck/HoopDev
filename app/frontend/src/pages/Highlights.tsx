import { useState, useEffect } from 'react'
import { listHighlights, deleteHighlight, streamUrl, thumbnailUrl, type HighlightClipMeta } from '../api/highlights'
import { Layout } from '../components/shared/Layout'
import { Button } from '../components/shared/Button'

function ClipPlayer({ clip, onClose }: { clip: HighlightClipMeta; onClose: () => void }) {
  return (
    <div
      className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div className="bg-gray-900 rounded-2xl overflow-hidden max-w-2xl w-full" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-800">
          <p className="text-sm text-gray-400">
            {clip.duration_s ? `${clip.duration_s.toFixed(1)}s` : 'Highlight clip'}
          </p>
          <button onClick={onClose} className="text-gray-500 hover:text-white text-lg leading-none">✕</button>
        </div>
        <video
          src={streamUrl(clip.id)}
          controls
          autoPlay
          className="w-full aspect-video bg-black"
        />
      </div>
    </div>
  )
}

export function Highlights() {
  const [clips, setClips] = useState<HighlightClipMeta[]>([])
  const [loading, setLoading] = useState(true)
  const [playing, setPlaying] = useState<HighlightClipMeta | null>(null)
  const [deleting, setDeleting] = useState<number | null>(null)

  useEffect(() => {
    listHighlights()
      .then(setClips)
      .catch(() => null)
      .finally(() => setLoading(false))
  }, [])

  async function handleDelete(id: number) {
    setDeleting(id)
    try {
      await deleteHighlight(id)
      setClips((prev) => prev.filter((c) => c.id !== id))
    } finally {
      setDeleting(null)
    }
  }

  return (
    <Layout title="Highlights">
      {loading ? (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {Array.from({ length: 8 }).map((_, i) => (
            <div key={i} className="aspect-video bg-gray-800 animate-pulse rounded-xl" />
          ))}
        </div>
      ) : clips.length === 0 ? (
        <div className="text-center py-24">
          <p className="text-gray-600 text-lg mb-2">No highlights yet</p>
          <p className="text-gray-700 text-sm">Make shots during a live session to auto-capture clips.</p>
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {clips.map((clip) => (
            <div key={clip.id} className="group relative bg-gray-900 rounded-xl overflow-hidden">
              {/* Thumbnail */}
              <div
                className="aspect-video bg-gray-800 cursor-pointer relative"
                onClick={() => setPlaying(clip)}
              >
                {clip.thumbnail_path ? (
                  <img
                    src={thumbnailUrl(clip.id)}
                    alt="Highlight thumbnail"
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="w-full h-full flex items-center justify-center">
                    <span className="text-gray-600 text-3xl">🏀</span>
                  </div>
                )}
                <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                  <span className="text-white text-3xl">▶</span>
                </div>
              </div>

              {/* Info + delete */}
              <div className="p-2 flex items-center justify-between">
                <p className="text-xs text-gray-500">
                  {clip.duration_s ? `${clip.duration_s.toFixed(1)}s` : 'clip'}
                </p>
                <Button
                  size="sm"
                  variant="ghost"
                  loading={deleting === clip.id}
                  onClick={() => handleDelete(clip.id)}
                  className="text-xs text-red-500 hover:text-red-400 px-2 py-1"
                >
                  Delete
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {playing && (
        <ClipPlayer clip={playing} onClose={() => setPlaying(null)} />
      )}
    </Layout>
  )
}

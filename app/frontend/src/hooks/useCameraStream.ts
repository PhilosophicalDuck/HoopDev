import { useState, useEffect } from 'react'

export function useCameraStream(cameraIndex = 0) {
  const token = localStorage.getItem('access_token')
  // MJPEG stream — browser decodes multipart/x-mixed-replace natively
  // We append a cache-busting timestamp so reconnects work
  const [streamUrl, setStreamUrl] = useState<string>('')

  useEffect(() => {
    // Build URL with auth token as query param (MJPEG img src can't send headers)
    const url = `/api/camera/stream?index=${cameraIndex}&t=${Date.now()}&token=${token}`
    setStreamUrl(url)
    return () => setStreamUrl('')
  }, [cameraIndex, token])

  return streamUrl
}

import { useState, useEffect, useRef } from 'react'
import { checkHealth } from '../services/api'

export function useHealthPoller(intervalMs = 3000) {
  const [status, setStatus] = useState({ online: null, latencyMs: null, mode: 'checking' })
  const timerRef = useRef(null)

  const poll = async () => {
    const result = await checkHealth()
    setStatus({
      online: result.online,
      latencyMs: result.latencyMs,
      mode: result.online ? 'live' : 'mock',
    })
  }

  useEffect(() => {
    poll()
    timerRef.current = setInterval(poll, intervalMs)
    return () => clearInterval(timerRef.current)
  }, [intervalMs])

  return status
}

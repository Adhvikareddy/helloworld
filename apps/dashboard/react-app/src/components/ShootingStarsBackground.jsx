import { useEffect, useRef } from 'react'

const STAR_COUNT = 12

function createStar(canvas) {
  const fromLeft = Math.random() > 0.5
  return {
    x: fromLeft ? Math.random() * canvas.width * 0.3 : Math.random() * canvas.width,
    y: fromLeft ? Math.random() * canvas.height * 0.3 : -10,
    speed: 2.5 + Math.random() * 3.5,
    length: 80 + Math.random() * 120,
    opacity: 0.7 + Math.random() * 0.3,
    width: 1 + Math.random() * 1.5,
    cyan: Math.random() > 0.6,
    life: 0,
    maxLife: 80 + Math.random() * 60,
  }
}

export default function ShootingStarsBackground() {
  const canvasRef = useRef(null)
  const starsRef = useRef([])
  const rafRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')

    const resize = () => {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
    }
    resize()
    window.addEventListener('resize', resize)

    // Initialise stars staggered
    starsRef.current = Array.from({ length: STAR_COUNT }, (_, i) => {
      const s = createStar(canvas)
      s.life = Math.floor((i / STAR_COUNT) * s.maxLife)
      return s
    })

    const draw = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      starsRef.current = starsRef.current.map(star => {
        const progress = star.life / star.maxLife
        const alpha = star.opacity * Math.sin(Math.PI * progress)

        // Tail gradient
        const tailX = star.x - star.length * 0.707
        const tailY = star.y - star.length * 0.707
        const grad = ctx.createLinearGradient(tailX, tailY, star.x, star.y)
        grad.addColorStop(0, `rgba(0,0,0,0)`)
        if (star.cyan) {
          grad.addColorStop(0.6, `rgba(79,172,254,${alpha * 0.4})`)
          grad.addColorStop(1, `rgba(0,242,254,${alpha})`)
        } else {
          grad.addColorStop(0.6, `rgba(200,220,255,${alpha * 0.4})`)
          grad.addColorStop(1, `rgba(255,255,255,${alpha})`)
        }

        ctx.beginPath()
        ctx.moveTo(tailX, tailY)
        ctx.lineTo(star.x, star.y)
        ctx.strokeStyle = grad
        ctx.lineWidth = star.width
        ctx.lineCap = 'round'
        ctx.stroke()

        // Bright head dot
        ctx.beginPath()
        ctx.arc(star.x, star.y, star.width * 0.8, 0, Math.PI * 2)
        ctx.fillStyle = star.cyan
          ? `rgba(0,242,254,${alpha})`
          : `rgba(255,255,255,${alpha})`
        ctx.fill()

        const next = {
          ...star,
          x: star.x + star.speed * 0.707,
          y: star.y + star.speed * 0.707,
          life: star.life + 1,
        }

        if (next.life >= next.maxLife) return createStar(canvas)
        return next
      })

      rafRef.current = requestAnimationFrame(draw)
    }

    rafRef.current = requestAnimationFrame(draw)

    return () => {
      cancelAnimationFrame(rafRef.current)
      window.removeEventListener('resize', resize)
    }
  }, [])

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        width: '100vw',
        height: '100vh',
        zIndex: -1,
        pointerEvents: 'none',
      }}
    />
  )
}

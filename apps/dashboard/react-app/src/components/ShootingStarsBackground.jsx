import { useEffect, useRef } from 'react'

export default function ShootingStarsBackground() {
  const canvasRef = useRef(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext('2d')

    let animationFrameId
    let particlesArray = []
    let shootingStars = []
    const numberOfParticles = 80

    function initDimensions() {
      canvas.width = window.innerWidth
      canvas.height = window.innerHeight
    }
    initDimensions()

    class Particle {
      constructor() {
        this.reset()
        this.x = Math.random() * canvas.width
        this.y = Math.random() * canvas.height
      }

      reset() {
        this.x = Math.random() * canvas.width
        this.y = Math.random() * canvas.height
        this.size = Math.random() * 1.3 + 0.3
        this.speedX = (Math.random() - 0.5) * 0.22
        this.speedY = (Math.random() - 0.5) * 0.22
        this.baseOpacity = Math.random() * 0.4 + 0.15
        this.opacity = this.baseOpacity
        this.pulseSpeed = Math.random() * 0.015 + 0.005
        this.pulseDir = Math.random() > 0.5 ? 1 : -1
      }

      update() {
        this.x += this.speedX
        this.y += this.speedY

        // Subtle twinkling
        this.opacity += this.pulseSpeed * this.pulseDir
        if (this.opacity > this.baseOpacity + 0.2) {
          this.pulseDir = -1
        } else if (this.opacity < Math.max(0.08, this.baseOpacity - 0.2)) {
          this.pulseDir = 1
        }

        if (this.x > canvas.width) this.x = 0
        else if (this.x < 0) this.x = canvas.width

        if (this.y > canvas.height) this.y = 0
        else if (this.y < 0) this.y = canvas.height
      }

      draw() {
        ctx.beginPath()
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(240, 244, 255, ${this.opacity})`
        ctx.fill()
      }
    }

    class ShootingStar {
      constructor() {
        this.reset()
      }

      reset() {
        this.x = Math.random() * (canvas.width * 0.7) + canvas.width * 0.1
        this.y = Math.random() * (canvas.height * 0.35)
        this.length = Math.random() * 70 + 40
        this.speed = Math.random() * 5 + 3.5
        this.angle = Math.PI / 4 // 45 degrees
        this.dx = Math.cos(this.angle) * this.speed
        this.dy = Math.sin(this.angle) * this.speed
        this.opacity = 0.75
        this.decay = Math.random() * 0.018 + 0.012
        this.active = false
      }

      launch() {
        this.reset()
        this.active = true
      }

      update() {
        if (!this.active) return
        this.x += this.dx
        this.y += this.dy
        this.opacity -= this.decay
        if (this.opacity <= 0) {
          this.active = false
        }
      }

      draw() {
        if (!this.active || this.opacity <= 0) return
        const tailX = this.x - Math.cos(this.angle) * this.length
        const tailY = this.y - Math.sin(this.angle) * this.length

        const grad = ctx.createLinearGradient(tailX, tailY, this.x, this.y)
        grad.addColorStop(0, 'rgba(255, 255, 255, 0)')
        grad.addColorStop(1, `rgba(255, 255, 255, ${this.opacity})`)

        ctx.beginPath()
        ctx.moveTo(tailX, tailY)
        ctx.lineTo(this.x, this.y)
        ctx.strokeStyle = grad
        ctx.lineWidth = 1.1
        ctx.stroke()
      }
    }

    function initParticles() {
      particlesArray = []
      for (let i = 0; i < numberOfParticles; i++) {
        particlesArray.push(new Particle())
      }
      shootingStars = [new ShootingStar(), new ShootingStar()]
    }
    initParticles()

    let nextLaunch = Date.now() + 2000

    const handleResize = () => {
      initDimensions()
      initParticles()
    }
    window.addEventListener('resize', handleResize)

    function animate() {
      ctx.clearRect(0, 0, canvas.width, canvas.height)

      // Draw background ambient stars
      for (let i = 0; i < particlesArray.length; i++) {
        particlesArray[i].update()
        particlesArray[i].draw()
      }

      // Shooting stars trigger
      const now = Date.now()
      if (now > nextLaunch) {
        const available = shootingStars.find(s => !s.active)
        if (available) {
          available.launch()
        }
        nextLaunch = now + Math.random() * 4500 + 3000
      }

      for (let s of shootingStars) {
        s.update()
        s.draw()
      }

      animationFrameId = requestAnimationFrame(animate)
    }
    animate()

    return () => {
      cancelAnimationFrame(animationFrameId)
      window.removeEventListener('resize', handleResize)
    }
  }, [])

  return (
    <div className="fixed inset-0 pointer-events-none z-0 overflow-hidden">
      {/* Pristine Deep Tech Vignette & Grid */}
      <div
        className="absolute inset-0"
        style={{
          background: 'radial-gradient(ellipse 80% 50% at 50% -10%, rgba(30, 41, 59, 0.25) 0%, rgba(9, 10, 13, 0) 80%)',
        }}
      />
      <div
        className="absolute inset-0 opacity-[0.035]"
        style={{
          backgroundImage: 'radial-gradient(rgba(255, 255, 255, 0.6) 1px, transparent 1px)',
          backgroundSize: '32px 32px',
          maskImage: 'radial-gradient(ellipse 70% 70% at 50% 40%, black 20%, transparent 80%)',
          WebkitMaskImage: 'radial-gradient(ellipse 70% 70% at 50% 40%, black 20%, transparent 80%)',
        }}
      />

      {/* Moving Stars Canvas */}
      <canvas
        ref={canvasRef}
        id="particleCanvas"
        className="absolute inset-0 w-full h-full"
      />
    </div>
  )
}

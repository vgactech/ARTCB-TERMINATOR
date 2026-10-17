/**
 * LivenessGate — KYC human-presence challenge (hand movement).
 *
 * The user must perform a random gesture shown by the backend. MediaPipe runs
 * locally in the browser; only a pixel-free observation (frames count, movement
 * score, directions, pinch ratio) is POSTed for verification. A "mode démo sans
 * caméra" path exists for offline demos and is always marked SIMULATED.
 */
import { forwardRef, useEffect, useImperativeHandle, useRef, useState } from 'react'
import { AlertTriangle, Camera, Hand, ShieldCheck } from 'lucide-react'
import {
  createLivenessChallenge,
  fetchLivenessStatus,
  verifyLiveness,
  type LivenessChallenge,
  type LivenessResult,
  type LivenessStatus,
} from '../api/guardian'
import { GestureDetector, type Landmark, type LivenessGestureId } from '../liveness/gesture'
import { loadHandLandmarker, HAND_CONNECTIONS, type HandLandmarkerLike } from '../liveness/handLandmarker'

export type LivenessOutcome = { token: string | null; status: string }

export type LivenessGateHandle = {
  start: () => void
  demo: () => void
}

type LivenessGateProps = {
  apiBase: string
  disabled?: boolean
  onVerified: (outcome: LivenessOutcome) => void
  /** Hide the built-in buttons (parent renders the controls instead). */
  showControls?: boolean
  /** Notify the parent when the gate is busy (loading/running/verifying). */
  onBusyChange?: (busy: boolean) => void
}

type Phase = 'idle' | 'loading' | 'camera' | 'running' | 'verifying' | 'done' | 'error'

const STATUS_COLOR: Record<string, string> = {
  PASS: '#6ee7b7',
  SIMULATED: '#fbbf24',
  FAIL: '#fda4af',
  SKIPPED: '#94a3b8',
}

export const LivenessGate = forwardRef<LivenessGateHandle, LivenessGateProps>(function LivenessGate(
  { apiBase, disabled, onVerified, showControls = true, onBusyChange },
  ref,
) {
  const [status, setStatus] = useState<LivenessStatus | null>(null)
  const [phase, setPhase] = useState<Phase>('idle')
  const [challenge, setChallenge] = useState<LivenessChallenge | null>(null)
  const [result, setResult] = useState<LivenessResult | null>(null)
  const [message, setMessage] = useState('')
  const [frameCount, setFrameCount] = useState(0)

  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const landmarkerRef = useRef<HandLandmarkerLike | null>(null)
  const detectorRef = useRef<GestureDetector | null>(null)
  const rafRef = useRef<number | null>(null)
  const activeRef = useRef(false)
  const deadlineRef = useRef(0)
  const challengeRef = useRef<LivenessChallenge | null>(null)

  useImperativeHandle(ref, () => ({
    start: () => { void startChallenge() },
    demo: () => { void runDemo() },
  }))

  const busy = phase === 'loading' || phase === 'running' || phase === 'verifying'

  useEffect(() => { onBusyChange?.(busy) }, [busy, onBusyChange])

  useEffect(() => {
    let alive = true
    fetchLivenessStatus()
      .then((s) => { if (alive) setStatus(s) })
      .catch(() => { if (alive) setMessage('Liveness indisponible — mode démo possible') })
    return () => { alive = false }
  }, [apiBase])

  function stopCamera() {
    activeRef.current = false
    if (rafRef.current !== null) cancelAnimationFrame(rafRef.current)
    rafRef.current = null
    streamRef.current?.getTracks().forEach((t) => t.stop())
    streamRef.current = null
    if (videoRef.current) videoRef.current.srcObject = null
    const canvas = canvasRef.current
    if (canvas) {
      const ctx = canvas.getContext('2d')
      ctx?.clearRect(0, 0, canvas.width, canvas.height)
    }
  }

  useEffect(() => () => stopCamera(), [])

  async function submitObservation(observation: Parameters<typeof verifyLiveness>[0]) {
    setPhase('verifying')
    try {
      const verdict = await verifyLiveness(observation)
      setResult(verdict)
      setPhase('done')
      onVerified({ token: challengeRef.current?.challenge_id ?? null, status: verdict.liveness })
    } catch (err) {
      setPhase('error')
      setMessage(err instanceof Error ? err.message : 'Vérification liveness échouée')
      onVerified({ token: null, status: 'FAIL' })
    } finally {
      stopCamera()
    }
  }

  function drawOverlay(hands: Landmark[][]) {
    const canvas = canvasRef.current
    const video = videoRef.current
    if (!canvas || !video) return
    canvas.width = video.videoWidth || 320
    canvas.height = video.videoHeight || 240
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    ctx.clearRect(0, 0, canvas.width, canvas.height)
    const w = canvas.width
    const h = canvas.height
    for (const hand of hands) {
      // Bones first, so joints render on top of the connections.
      ctx.strokeStyle = '#34d399'
      ctx.lineWidth = 3
      ctx.lineCap = 'round'
      for (const [a, b] of HAND_CONNECTIONS) {
        const p1 = hand[a]
        const p2 = hand[b]
        if (!p1 || !p2) continue
        ctx.beginPath()
        ctx.moveTo(p1.x * w, p1.y * h)
        ctx.lineTo(p2.x * w, p2.y * h)
        ctx.stroke()
      }
      ctx.fillStyle = '#a7f3d0'
      for (const lm of hand) {
        ctx.beginPath()
        ctx.arc(lm.x * w, lm.y * h, 3, 0, Math.PI * 2)
        ctx.fill()
      }
    }
  }

  function loop() {
    if (!activeRef.current) return
    const video = videoRef.current
    const landmarker = landmarkerRef.current
    const detector = detectorRef.current
    if (video && landmarker && detector && video.readyState >= 2) {
      let hands: Landmark[][] = []
      try {
        const res = landmarker.detectForVideo(video, performance.now())
        hands = res?.landmarks ?? []
      } catch {
        stopCamera()
        setPhase('camera')
        setMessage('Détection MediaPipe interrompue — utilisez le mode démo.')
        return
      }
      drawOverlay(hands)
      if (hands[0]) {
        detector.addFrame(hands[0].map((l) => ({ x: 1 - l.x, y: l.y })))
        setFrameCount(detector.frameCount)
        if (detector.evaluate().gesture_matched) {
          void finish(detector.evaluate())
          return
        }
      }
      if (performance.now() > deadlineRef.current) {
        void finish(detector.evaluate())
        return
      }
    }
    rafRef.current = requestAnimationFrame(loop)
  }

  async function finish(observation: ReturnType<GestureDetector['evaluate']>) {
    activeRef.current = false
    const ch = challengeRef.current
    if (!ch) return
    await submitObservation({ ...observation, challenge_id: ch.challenge_id, nonce: ch.nonce })
  }

  async function startChallenge() {
    setResult(null)
    setFrameCount(0)
    setMessage('')
    try {
      const ch = await createLivenessChallenge()
      challengeRef.current = ch
      setChallenge(ch)
    } catch (err) {
      setPhase('error')
      setMessage(err instanceof Error ? err.message : 'Défi indisponible')
      return
    }

    setPhase('loading')
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: 640, height: 480 },
      })
      streamRef.current = stream
      const video = videoRef.current
      if (video) {
        video.srcObject = stream
        await video.play()
      }
      landmarkerRef.current = await loadHandLandmarker()
      const ch = challengeRef.current!
      detectorRef.current = new GestureDetector(ch.gesture as LivenessGestureId)
      deadlineRef.current = performance.now() + ch.ttl_seconds * 1000
      activeRef.current = true
      setPhase('running')
      rafRef.current = requestAnimationFrame(loop)
    } catch {
      stopCamera()
      setPhase('camera')
      setMessage('Caméra ou modèle MediaPipe indisponible — utilisez le mode démo.')
    }
  }

  async function runDemo() {
    setResult(null)
    setFrameCount(0)
    setMessage('')
    try {
      const ch = await createLivenessChallenge()
      challengeRef.current = ch
      setChallenge(ch)
      await submitObservation({
        challenge_id: ch.challenge_id,
        nonce: ch.nonce,
        gesture: ch.gesture,
        hand_frames: 0,
        movement_score: 0,
        directions: [],
        pinch_ratio: null,
        gesture_matched: false,
        duration_ms: 0,
        simulated: true,
      })
    } catch (err) {
      setPhase('error')
      setMessage(err instanceof Error ? err.message : 'Mode démo indisponible')
      onVerified({ token: null, status: 'SKIPPED' })
    }
  }

  const statusColor = result ? STATUS_COLOR[result.liveness] ?? '#94a3b8' : '#94a3b8'

  return (
    <div style={{ background: 'rgba(15,23,42,0.55)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 12, padding: 14, display: 'flex', flexDirection: 'column', gap: 10 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
        <Hand size={15} color="#a5b4fc" />
        <span style={{ fontSize: 12, fontWeight: 700, color: '#e2e8f0' }}>Preuve de présence humaine</span>
        {status && (
          <span style={{ marginLeft: 'auto', fontSize: 10, color: status.enabled ? '#6ee7b7' : '#fbbf24' }}>
            {status.enabled ? 'liveness actif' : 'liveness désactivé (simulé)'}
          </span>
        )}
      </div>

      <div style={{ position: 'relative', width: '100%', aspectRatio: '16 / 9', maxHeight: 340, background: '#020617', borderRadius: 10, overflow: 'hidden', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <video
          ref={videoRef}
          muted
          playsInline
          style={{ width: '100%', height: '100%', objectFit: 'cover', transform: 'scaleX(-1)', display: phase === 'running' || phase === 'verifying' ? 'block' : 'none' }}
        />
        <canvas ref={canvasRef} style={{ position: 'absolute', inset: 0, width: '100%', height: '100%', transform: 'scaleX(-1)', pointerEvents: 'none' }} />
        {phase !== 'running' && phase !== 'verifying' && (
          <div style={{ textAlign: 'center', padding: 12 }}>
            <Camera size={22} color="#475569" />
            <p style={{ margin: '6px 0 0', fontSize: 11, color: '#64748b' }}>
              {message || 'Aucune caméra active'}
            </p>
          </div>
        )}
      </div>

      {challenge && (
        <div style={{ background: 'rgba(99,102,241,0.1)', border: '1px solid rgba(99,102,241,0.3)', borderRadius: 8, padding: '8px 10px' }}>
          <p style={{ margin: 0, fontSize: 11, color: '#c7d2fe' }}>{challenge.instruction_fr}</p>
          <p style={{ margin: '2px 0 0', fontSize: 10, color: '#64748b' }}>
            Défi : {challenge.gesture} · {frameCount} image(s) · expire dans {challenge.ttl_seconds}s
          </p>
        </div>
      )}

      {result && (
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 7, background: `${statusColor}14`, border: `1px solid ${statusColor}55`, borderRadius: 8, padding: '8px 10px' }}>
          <ShieldCheck size={14} color={statusColor} style={{ marginTop: 2, flexShrink: 0 }} />
          <div>
            <p style={{ margin: 0, fontSize: 11, fontWeight: 700, color: statusColor }}>
              {result.liveness} — {result.human_proven ? 'humain prouvé' : 'humain non prouvé'}
            </p>
            <p style={{ margin: '2px 0 0', fontSize: 10, color: '#94a3b8' }}>{result.reason}</p>
          </div>
        </div>
      )}

      {message && phase === 'error' && (
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 10, color: '#fda4af' }}>
          <AlertTriangle size={12} /> {message}
        </div>
      )}

      {showControls && (
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <button
            type="button"
            onClick={startChallenge}
            disabled={disabled || busy}
            style={{
              flex: '1 1 150px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6,
              background: 'rgba(99,102,241,0.15)', border: '1px solid rgba(99,102,241,0.4)',
              borderRadius: 10, padding: '9px 12px', fontSize: 12, fontWeight: 600,
              color: '#c7d2fe', cursor: disabled || busy ? 'wait' : 'pointer',
              opacity: disabled || busy ? 0.6 : 1,
            }}
          >
            <Camera size={14} /> {busy ? 'Défi en cours…' : 'Démarrer le défi (caméra)'}
          </button>
          <button
            type="button"
            onClick={runDemo}
            disabled={disabled || busy}
            title="Aucune caméra requise — résultat marqué SIMULATED"
            style={{
              flex: '0 0 auto', display: 'flex', alignItems: 'center', gap: 6,
              background: 'rgba(15,23,42,0.7)', border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: 10, padding: '9px 12px', fontSize: 12, fontWeight: 600,
              color: '#94a3b8', cursor: disabled || busy ? 'not-allowed' : 'pointer',
              opacity: disabled || busy ? 0.5 : 1,
            }}
          >
            Mode démo sans caméra
          </button>
        </div>
      )}
    </div>
  )
})

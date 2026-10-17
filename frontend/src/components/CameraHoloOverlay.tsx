/**
 * CameraHoloOverlay — ARTCB TERMINATOR FORENSIC
 *
 * R096 — Caméra + MediaPipe Face Landmarker + overlay holographique 2D animé.
 *
 * États caméra (5) :
 *   idle       → caméra éteinte par défaut
 *   requesting → attente de la permission navigateur
 *   active     → flux vidéo + détection faciale en cours
 *   denied     → permission refusée (guide utilisateur affiché)
 *   error      → erreur matérielle ou contrainte caméra
 *
 * Architecture :
 *   • getUserMedia() → <video> → requestAnimationFrame → canvas overlay
 *   • MediaPipe FaceLandmarker (WASM, CDN offload, chargement lazy)
 *   • Overlay = triangles holographiques + contour visage + points clés
 *   • Boucle RAF indépendante du flux SSE (aucun couplage KYC direct)
 *   • Libération complète de toutes les pistes vidéo à l'arrêt/unmount
 *
 * Décisions architecturales :
 *   • Pas de Three.js (overhead ~500 KB, incompatible deadline compétition)
 *   • Canvas 2D suffit pour un effet holographique convaincant en jury
 *   • FaceLandmarker en mode VIDEO (runningMode = "VIDEO")
 *   • Fail-open sur MediaPipe : si le modèle ne charge pas, la caméra
 *     continue de s'afficher sans overlay facial (dégradation gracieuse)
 *   • unique_human_proven=false — la détection faciale ≠ identité légale
 *
 * CERTIFIED_100=false | unique_human_proven=false | Mode DEBUG actif
 */

import { useCallback, useEffect, useRef, useState } from 'react'
import { Camera, CameraOff, AlertTriangle, Loader2 } from 'lucide-react'

// ── Types ─────────────────────────────────────────────────────────────────────

export type CameraState = 'idle' | 'requesting' | 'active' | 'denied' | 'error'

export type HoloOverlayProps = {
  /** Appelé quand l'état change — permet au parent de coordonner le flux KYC */
  onStateChange?: (state: CameraState) => void
  /** Si true, désactive les contrôles (pendant un KYC en cours) */
  kycRunning?: boolean
}

// ── MediaPipe types (sous-ensemble minimal pour le type-checking) ─────────────
// On évite d'importer directement le module complet pour contrôler le tree-shaking.

type Landmark = { x: number; y: number; z: number }
type FaceLandmarkerResult = { faceLandmarks: Landmark[][] }

interface FaceLandmarkerInstance {
  detectForVideo(video: HTMLVideoElement, timestamp: number): FaceLandmarkerResult
  close(): void
}

// ── Constantes hologramme ─────────────────────────────────────────────────────

// Indices des points clés MediaPipe (478 landmarks) — sous-ensemble expressif
const CONTOUR_INDICES = [
  // Contour du visage (face oval)
  10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288,
  397, 365, 379, 378, 400, 377, 152, 148, 176, 149, 150, 136,
  172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109,
]

const TRIANGLE_GROUPS: [number, number, number][] = [
  // Triangles bridge nez-yeux (effet maillage holographique)
  [33, 133, 159], [133, 159, 145], [362, 263, 386], [263, 386, 374],
  // Bouche
  [61, 291, 13], [291, 13, 14], [61, 14, 17],
  // Front
  [10, 67, 297], [67, 297, 109],
  // Mâchoire
  [152, 377, 378], [377, 378, 400],
]

// Couleurs holographiques
const HOLO_CYAN   = 'rgba(34, 211, 238, '   // cyan-400
const HOLO_GREEN  = 'rgba(52, 211, 153, '   // emerald-400
const HOLO_VIOLET = 'rgba(167, 139, 250, '  // violet-400

// ── Helpers ───────────────────────────────────────────────────────────────────

function lm(landmarks: Landmark[], i: number, w: number, h: number): [number, number] {
  const p = landmarks[i]
  if (!p) return [0, 0]
  return [p.x * w, p.y * h]
}

// ── Chargement lazy MediaPipe ─────────────────────────────────────────────────

let _landmarkerPromise: Promise<FaceLandmarkerInstance | null> | null = null

async function loadFaceLandmarker(): Promise<FaceLandmarkerInstance | null> {
  if (_landmarkerPromise) return _landmarkerPromise
  _landmarkerPromise = (async () => {
    try {
      // Import dynamique — tree-shaking propre, chargement lazy
      const { FaceLandmarker, FilesetResolver } = await import(
        /* @vite-ignore */ '@mediapipe/tasks-vision'
      )
      const vision = await FilesetResolver.forVisionTasks(
        // CDN officiel MediaPipe WASM — évite de bundler ~4 MB dans le dist
        'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.22/wasm'
      )
      const landmarker = await FaceLandmarker.createFromOptions(vision, {
        baseOptions: {
          modelAssetPath:
            'https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task',
          delegate: 'GPU',
        },
        runningMode: 'VIDEO',
        numFaces: 1,
        outputFaceBlendshapes: false,
      })
      console.debug('[CameraHoloOverlay] MediaPipe FaceLandmarker chargé')
      return landmarker as FaceLandmarkerInstance
    } catch (err) {
      console.warn('[CameraHoloOverlay] MediaPipe non disponible — overlay désactivé', err)
      _landmarkerPromise = null // autoriser un retry
      return null
    }
  })()
  return _landmarkerPromise
}

// ── Dessin overlay holographique ──────────────────────────────────────────────

function drawHoloOverlay(
  ctx: CanvasRenderingContext2D,
  landmarks: Landmark[],
  w: number,
  h: number,
  tick: number,
) {
  ctx.clearRect(0, 0, w, h)

  if (!landmarks || landmarks.length === 0) return

  const pulse = 0.5 + 0.5 * Math.sin(tick * 0.06)   // 0…1 oscillant
  const scan  = (tick * 1.5) % h                     // ligne de scan verticale

  // ── 1. Triangles maillage ──────────────────────────────────────────────────
  for (const [a, b, c] of TRIANGLE_GROUPS) {
    const [x0, y0] = lm(landmarks, a, w, h)
    const [x1, y1] = lm(landmarks, b, w, h)
    const [x2, y2] = lm(landmarks, c, w, h)
    ctx.beginPath()
    ctx.moveTo(x0, y0)
    ctx.lineTo(x1, y1)
    ctx.lineTo(x2, y2)
    ctx.closePath()
    ctx.fillStyle   = `${HOLO_CYAN}${0.04 + 0.04 * pulse})`
    ctx.strokeStyle = `${HOLO_CYAN}${0.45 + 0.3 * pulse})`
    ctx.lineWidth   = 0.8
    ctx.fill()
    ctx.stroke()
  }

  // ── 2. Contour du visage ───────────────────────────────────────────────────
  ctx.beginPath()
  CONTOUR_INDICES.forEach((i, idx) => {
    const [x, y] = lm(landmarks, i, w, h)
    if (idx === 0) ctx.moveTo(x, y)
    else           ctx.lineTo(x, y)
  })
  ctx.closePath()
  ctx.strokeStyle = `${HOLO_GREEN}${0.7 + 0.3 * pulse})`
  ctx.lineWidth   = 1.5
  ctx.shadowColor = `${HOLO_GREEN}0.8)`
  ctx.shadowBlur  = 6
  ctx.stroke()
  ctx.shadowBlur  = 0

  // ── 3. Points clés (yeux, nez, bouche) ────────────────────────────────────
  const keyPts = [1, 4, 6, 33, 133, 263, 362, 61, 291, 152, 10]
  for (const i of keyPts) {
    const [x, y] = lm(landmarks, i, w, h)
    ctx.beginPath()
    ctx.arc(x, y, 2.5, 0, Math.PI * 2)
    ctx.fillStyle = `${HOLO_VIOLET}${0.8 + 0.2 * pulse})`
    ctx.fill()
  }

  // ── 4. Ligne de scan holographique ────────────────────────────────────────
  const scanGrad = ctx.createLinearGradient(0, scan - 10, 0, scan + 10)
  scanGrad.addColorStop(0,   `${HOLO_CYAN}0)`)
  scanGrad.addColorStop(0.5, `${HOLO_CYAN}0.25)`)
  scanGrad.addColorStop(1,   `${HOLO_CYAN}0)`)
  ctx.fillStyle = scanGrad
  ctx.fillRect(0, scan - 10, w, 20)

  // ── 5. Coin HUD gauche ────────────────────────────────────────────────────
  ctx.fillStyle   = `${HOLO_CYAN}${0.7 + 0.3 * pulse})`
  ctx.font        = '9px ui-monospace, monospace'
  ctx.fillText('BIOMETRIC SCAN', 8, 16)
  ctx.fillStyle   = `${HOLO_GREEN}0.9)`
  ctx.fillText('FACE DETECTED ✓', 8, 28)
  ctx.fillStyle   = `rgba(148,163,184,0.6)`
  ctx.fillText(`unique_human_proven=false`, 8, h - 8)
}

// ── Composant principal ───────────────────────────────────────────────────────

export function CameraHoloOverlay({ onStateChange, kycRunning = false }: HoloOverlayProps) {
  const [camState,    setCamState]    = useState<CameraState>('idle')
  const [mpReady,     setMpReady]     = useState(false)
  const [faceCount,   setFaceCount]   = useState(0)

  const videoRef      = useRef<HTMLVideoElement>(null)
  const canvasRef     = useRef<HTMLCanvasElement>(null)
  const streamRef     = useRef<MediaStream | null>(null)
  const landmarkerRef = useRef<FaceLandmarkerInstance | null>(null)
  const rafRef        = useRef<number>(0)
  const tickRef       = useRef<number>(0)

  // Notifie le parent à chaque changement d'état
  const setAndNotify = useCallback((s: CameraState) => {
    setCamState(s)
    onStateChange?.(s)
  }, [onStateChange])

  // ── Libération complète des ressources ─────────────────────────────────────
  const stopCamera = useCallback(() => {
    cancelAnimationFrame(rafRef.current)
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop())
      streamRef.current = null
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null
    }
    if (canvasRef.current) {
      const ctx = canvasRef.current.getContext('2d')
      if (ctx) ctx.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height)
    }
  }, [])

  // Libération à l'unmount
  useEffect(() => {
    return () => {
      cancelAnimationFrame(rafRef.current)
      stopCamera()
    }
  }, [stopCamera])

  // ── Boucle RAF : détection + overlay ──────────────────────────────────────
  const startRaf = useCallback(() => {
    const video  = videoRef.current
    const canvas = canvasRef.current
    if (!video || !canvas) return

    const loop = () => {
      if (!videoRef.current || videoRef.current.readyState < 2) {
        rafRef.current = requestAnimationFrame(loop)
        return
      }
      const w = video.videoWidth  || 640
      const h = video.videoHeight || 480
      canvas.width  = w
      canvas.height = h
      const ctx = canvas.getContext('2d')
      if (!ctx) { rafRef.current = requestAnimationFrame(loop); return }

      tickRef.current += 1

      if (landmarkerRef.current) {
        try {
          const result = landmarkerRef.current.detectForVideo(video, performance.now())
          const faces  = result.faceLandmarks ?? []
          setFaceCount(faces.length)
          if (faces.length > 0) {
            drawHoloOverlay(ctx, faces[0], w, h, tickRef.current)
          } else {
            ctx.clearRect(0, 0, w, h)
            // Affichage minimal même sans visage
            drawScanOnly(ctx, w, h, tickRef.current)
          }
        } catch {
          ctx.clearRect(0, 0, w, h)
        }
      } else {
        // MediaPipe pas encore chargé : affichage scan seul
        ctx.clearRect(0, 0, w, h)
        drawScanOnly(ctx, w, h, tickRef.current)
      }

      rafRef.current = requestAnimationFrame(loop)
    }
    rafRef.current = requestAnimationFrame(loop)
  }, [])

  // ── Activation caméra ──────────────────────────────────────────────────────
  const startCamera = useCallback(async () => {
    if (camState === 'active' || camState === 'requesting') return
    setAndNotify('requesting')

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' },
        audio: false,
      })
      streamRef.current = stream

      if (videoRef.current) {
        videoRef.current.srcObject = stream
        await videoRef.current.play()
      }

      setAndNotify('active')
      startRaf()

      // Chargement MediaPipe en parallèle (non bloquant pour la vidéo)
      loadFaceLandmarker().then(fl => {
        landmarkerRef.current = fl
        setMpReady(fl !== null)
      })

    } catch (err) {
      const name = (err as Error).name ?? ''
      if (name === 'NotAllowedError' || name === 'PermissionDeniedError') {
        setAndNotify('denied')
      } else {
        setAndNotify('error')
      }
      console.debug('[CameraHoloOverlay] getUserMedia erreur :', err)
    }
  }, [camState, setAndNotify, startRaf])

  // ── Arrêt caméra ───────────────────────────────────────────────────────────
  const handleStop = useCallback(() => {
    stopCamera()
    setFaceCount(0)
    setAndNotify('idle')
  }, [stopCamera, setAndNotify])

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div style={{ position: 'relative', width: '100%', borderRadius: 12, overflow: 'hidden', background: '#060d1a', border: '1px solid rgba(34,211,238,0.15)' }}>

      {/* Conteneur vidéo + canvas overlay empilés */}
      <div style={{ position: 'relative', width: '100%', aspectRatio: '4/3', background: '#030810' }}>
        <video
          ref={videoRef}
          muted
          playsInline
          autoPlay
          style={{
            width: '100%', height: '100%',
            objectFit: 'cover',
            display: camState === 'active' ? 'block' : 'none',
            transform: 'scaleX(-1)', // miroir naturel
          }}
        />
        {/* Canvas holographique superposé */}
        <canvas
          ref={canvasRef}
          style={{
            position: 'absolute', inset: 0,
            width: '100%', height: '100%',
            pointerEvents: 'none',
            display: camState === 'active' ? 'block' : 'none',
            transform: 'scaleX(-1)',
          }}
        />

        {/* Overlay état : idle */}
        {camState === 'idle' && (
          <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 12 }}>
            <div style={{ width: 56, height: 56, borderRadius: '50%', border: '1px solid rgba(34,211,238,0.3)', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'rgba(34,211,238,0.06)' }}>
              <Camera size={24} color="rgba(34,211,238,0.6)" />
            </div>
            <p style={{ margin: 0, fontSize: 12, color: '#64748b', textAlign: 'center' }}>Caméra inactive</p>
            <p style={{ margin: 0, fontSize: 10, color: '#334155', textAlign: 'center', maxWidth: 200 }}>
              Activez la caméra pour le scan biométrique holographique
            </p>
          </div>
        )}

        {/* Overlay état : requesting */}
        {camState === 'requesting' && (
          <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 12 }}>
            <Loader2 size={28} color="#22d3ee" style={{ animation: 'spin 1s linear infinite' }} />
            <p style={{ margin: 0, fontSize: 12, color: '#22d3ee' }}>Demande de permission…</p>
            <p style={{ margin: 0, fontSize: 10, color: '#475569', textAlign: 'center', maxWidth: 200 }}>
              Autorisez l'accès caméra dans la barre du navigateur
            </p>
          </div>
        )}

        {/* Overlay état : denied */}
        {camState === 'denied' && (
          <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 12, padding: 16 }}>
            <AlertTriangle size={28} color="#f59e0b" />
            <p style={{ margin: 0, fontSize: 12, color: '#fbbf24', fontWeight: 600 }}>Permission refusée</p>
            <p style={{ margin: 0, fontSize: 10, color: '#64748b', textAlign: 'center', maxWidth: 220, lineHeight: 1.5 }}>
              Autorisez l'accès caméra dans les paramètres du navigateur (🔒 dans la barre d'adresse), puis réessayez.
            </p>
          </div>
        )}

        {/* Overlay état : error */}
        {camState === 'error' && (
          <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 12 }}>
            <CameraOff size={28} color="#f43f5e" />
            <p style={{ margin: 0, fontSize: 12, color: '#fda4af' }}>Caméra inaccessible</p>
            <p style={{ margin: 0, fontSize: 10, color: '#64748b', textAlign: 'center', maxWidth: 200 }}>
              Vérifiez qu'aucune autre application n'utilise la caméra.
            </p>
          </div>
        )}

        {/* Badge MediaPipe + face count (visible si actif) */}
        {camState === 'active' && (
          <div style={{ position: 'absolute', top: 8, left: 8, display: 'flex', gap: 6 }}>
            <span style={{
              fontSize: 9, fontFamily: 'ui-monospace,monospace',
              padding: '2px 7px', borderRadius: 20,
              background: mpReady ? 'rgba(16,185,129,0.15)' : 'rgba(100,116,139,0.15)',
              border: `1px solid ${mpReady ? 'rgba(16,185,129,0.4)' : 'rgba(100,116,139,0.3)'}`,
              color: mpReady ? '#34d399' : '#94a3b8',
            }}>
              {mpReady ? 'MediaPipe ✓' : 'MP loading…'}
            </span>
            {faceCount > 0 && (
              <span style={{
                fontSize: 9, fontFamily: 'ui-monospace,monospace',
                padding: '2px 7px', borderRadius: 20,
                background: 'rgba(34,211,238,0.12)',
                border: '1px solid rgba(34,211,238,0.35)',
                color: '#22d3ee',
              }}>
                {faceCount} visage{faceCount > 1 ? 's' : ''}
              </span>
            )}
          </div>
        )}
      </div>

      {/* Barre de contrôles */}
      <div style={{ padding: '10px 14px', borderTop: '1px solid rgba(255,255,255,0.06)', display: 'flex', alignItems: 'center', gap: 8, justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', gap: 8 }}>
          {camState !== 'active' ? (
            <button
              onClick={startCamera}
              disabled={camState === 'requesting' || kycRunning}
              style={{
                display: 'flex', alignItems: 'center', gap: 6,
                padding: '7px 14px', borderRadius: 8,
                background: camState === 'denied' || camState === 'error'
                  ? 'rgba(251,191,36,0.1)' : 'rgba(34,211,238,0.1)',
                border: `1px solid ${camState === 'denied' || camState === 'error'
                  ? 'rgba(251,191,36,0.35)' : 'rgba(34,211,238,0.3)'}`,
                color: camState === 'denied' || camState === 'error' ? '#fbbf24' : '#22d3ee',
                fontSize: 12, fontWeight: 600, cursor: 'pointer',
                opacity: (camState === 'requesting' || kycRunning) ? 0.5 : 1,
              }}
            >
              <Camera size={13} />
              {camState === 'denied' ? 'Réessayer caméra' :
               camState === 'error'  ? 'Relancer caméra'  :
               camState === 'requesting' ? 'En attente…' :
               'Activer la caméra'}
            </button>
          ) : (
            <button
              onClick={handleStop}
              style={{
                display: 'flex', alignItems: 'center', gap: 6,
                padding: '7px 14px', borderRadius: 8,
                background: 'rgba(244,63,94,0.08)',
                border: '1px solid rgba(244,63,94,0.3)',
                color: '#fda4af',
                fontSize: 12, fontWeight: 600, cursor: 'pointer',
              }}
            >
              <CameraOff size={13} />
              Arrêter la caméra
            </button>
          )}
        </div>

        {/* Avertissement CERTIFIED_100=false */}
        <span style={{ fontSize: 9, color: '#334155', fontFamily: 'ui-monospace,monospace' }}>
          CERTIFIED_100=false
        </span>
      </div>

      {/* Spin keyframe injecté inline */}
      <style>{`
        @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
      `}</style>
    </div>
  )
}

// ── Scan seul (sans visage détecté) ──────────────────────────────────────────

function drawScanOnly(ctx: CanvasRenderingContext2D, w: number, h: number, tick: number) {
  const scan = (tick * 1.5) % h
  const grad = ctx.createLinearGradient(0, scan - 10, 0, scan + 10)
  grad.addColorStop(0,   'rgba(34,211,238,0)')
  grad.addColorStop(0.5, 'rgba(34,211,238,0.15)')
  grad.addColorStop(1,   'rgba(34,211,238,0)')
  ctx.fillStyle = grad
  ctx.fillRect(0, scan - 10, w, 20)

  ctx.fillStyle = 'rgba(34,211,238,0.5)'
  ctx.font      = '9px ui-monospace, monospace'
  ctx.fillText('SCANNING…', 8, 16)
  ctx.fillStyle = 'rgba(148,163,184,0.5)'
  ctx.fillText('Aucun visage détecté', 8, 28)
}

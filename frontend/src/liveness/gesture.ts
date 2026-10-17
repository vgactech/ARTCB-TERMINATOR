/**
 * gesture.ts — pure hand-landmark analysis for the KYC liveness challenge.
 *
 * No DOM, no MediaPipe dependency: the caller feeds normalized landmarks
 * (MediaPipe HandLandmarker output, or synthetic data in tests) and receives a
 * pixel-free observation to POST to /api/liveness/verify.
 *
 * Coordinate convention: x,y in [0,1] image space (y grows downward), already
 * mirrored by the caller so "right" matches the user's perceived direction.
 */

export type Point = { x: number; y: number }
export type Landmark = { x: number; y: number; z?: number }
export type LivenessGestureId = 'left_to_right' | 'raise_hand' | 'pinch' | 'wave'

export type LivenessObservation = {
  gesture: LivenessGestureId
  hand_frames: number
  movement_score: number
  directions: string[]
  pinch_ratio: number | null
  gesture_matched: boolean
  duration_ms: number
}

export const GESTURE_IDS: LivenessGestureId[] = [
  'left_to_right',
  'raise_hand',
  'pinch',
  'wave',
]

// MediaPipe hand-landmark indices we depend on.
const WRIST = 0
const THUMB_TIP = 4
const INDEX_TIP = 8
const INDEX_MCP = 5
const MIDDLE_MCP = 9
const PINKY_MCP = 17

const DIRECTION_STEP = 0.02
const PINCH_CLOSED = 0.5
const PINCH_OPEN = 0.75

// Per-gesture validation bounds (kept consistent with guardian_api/liveness.py).
const MIN_FRAMES: Record<LivenessGestureId, number> = {
  left_to_right: 10,
  raise_hand: 8,
  pinch: 8,
  wave: 12,
}
const MIN_MOVEMENT: Record<LivenessGestureId, number> = {
  left_to_right: 0.15,
  raise_hand: 0.08,
  pinch: 0.02,
  wave: 0.18,
}

function span(values: number[]): number {
  if (values.length === 0) return 0
  let min = values[0]
  let max = values[0]
  for (const v of values) {
    if (v < min) min = v
    if (v > max) max = v
  }
  return max - min
}

/** Stable hand center from three reference joints (less jitter than one joint). */
export function handCenter(lm: Landmark[]): Point {
  const a = lm[WRIST]
  const b = lm[INDEX_MCP]
  const c = lm[PINKY_MCP]
  return { x: (a.x + b.x + c.x) / 3, y: (a.y + b.y + c.y) / 3 }
}

/** Thumb-to-index distance normalized by hand size (scale-invariant pinch proxy). */
export function pinchRatio(lm: Landmark[]): number {
  const thumb = lm[THUMB_TIP]
  const index = lm[INDEX_TIP]
  const wrist = lm[WRIST]
  const middle = lm[MIDDLE_MCP]
  const handSize = Math.hypot(wrist.x - middle.x, wrist.y - middle.y) || 1e-6
  return Math.hypot(thumb.x - index.x, thumb.y - index.y) / handSize
}

function directionsOf(centers: Point[]): string[] {
  const out: string[] = []
  for (let i = 1; i < centers.length; i++) {
    const dx = centers[i].x - centers[i - 1].x
    const dy = centers[i].y - centers[i - 1].y
    let dir: string | null = null
    if (Math.abs(dx) >= DIRECTION_STEP && Math.abs(dx) >= Math.abs(dy)) {
      dir = dx > 0 ? 'right' : 'left'
    } else if (Math.abs(dy) >= DIRECTION_STEP) {
      dir = dy > 0 ? 'down' : 'up'
    }
    if (dir && out[out.length - 1] !== dir) out.push(dir)
  }
  return out
}

function reversals(dirs: string[]): number {
  let count = 0
  for (let i = 1; i < dirs.length; i++) {
    if (dirs[i] !== dirs[i - 1]) count++
  }
  return count
}

/** Count closed-pinch episodes (thumb-index close, then reopen). */
function countPinches(ratios: number[]): number {
  let count = 0
  let closed = false
  for (const r of ratios) {
    if (!closed && r < PINCH_CLOSED) {
      closed = true
      count++
    } else if (closed && r > PINCH_OPEN) {
      closed = false
    }
  }
  return count
}

/** Analyze a landmark trajectory against the requested gesture. */
export function analyze(
  gesture: LivenessGestureId,
  frames: Landmark[][],
): LivenessObservation {
  const usable = frames.filter((f) => f && f.length >= 21)
  const centers = usable.map(handCenter)
  const pinches = usable.map(pinchRatio)
  const n = usable.length

  const hSpan = span(centers.map((c) => c.x))
  const vSpan = span(centers.map((c) => c.y))
  let movement = Math.hypot(hSpan, vSpan)
  let matched = false

  if (n > 0) {
    const first = centers[0]
    const last = centers[n - 1]
    const dirs = directionsOf(centers)
    switch (gesture) {
      case 'left_to_right':
        matched =
          n >= MIN_FRAMES.left_to_right &&
          hSpan >= MIN_MOVEMENT.left_to_right &&
          hSpan > vSpan &&
          last.x > first.x
        break
      case 'raise_hand':
        matched =
          n >= MIN_FRAMES.raise_hand &&
          vSpan >= MIN_MOVEMENT.raise_hand &&
          vSpan >= hSpan &&
          last.y < first.y
        break
      case 'pinch':
        movement = Math.max(movement, span(pinches))
        matched = n >= MIN_FRAMES.pinch && countPinches(pinches) >= 2
        break
      case 'wave':
        matched =
          n >= MIN_FRAMES.wave &&
          hSpan >= MIN_MOVEMENT.wave &&
          reversals(dirs) >= 2
        break
    }
  }

  return {
    gesture,
    hand_frames: n,
    movement_score: Number(movement.toFixed(4)),
    directions: n > 1 ? directionsOf(centers) : [],
    pinch_ratio: n > 0 ? Number(pinches[pinches.length - 1].toFixed(4)) : null,
    gesture_matched: matched,
    duration_ms: n * 33, // ~30 fps sampling estimate
  }
}

/**
 * Stateful detector: keeps an in-memory landmark window and evaluates on demand.
 * Landmarks never leave the browser — only the derived observation does.
 */
export class GestureDetector {
  private gesture: LivenessGestureId
  private maxFrames: number
  private frames: Landmark[][]

  constructor(gesture: LivenessGestureId, maxFrames = 240) {
    this.gesture = gesture
    this.maxFrames = maxFrames
    this.frames = []
  }

  addFrame(landmarks: Landmark[]): void {
    if (!landmarks || landmarks.length < 21) return
    this.frames.push(landmarks)
    if (this.frames.length > this.maxFrames) this.frames.shift()
  }

  get frameCount(): number {
    return this.frames.length
  }

  reset(): void {
    this.frames = []
  }

  evaluate(): LivenessObservation {
    return analyze(this.gesture, this.frames)
  }
}

/**
 * handLandmarker.ts — loads MediaPipe Tasks Vision HandLandmarker at runtime.
 *
 * The library + WASM + model are fetched from a CDN (jsDelivr / Google Storage)
 * so the Vite bundle stays small and we do not need a build-time dependency.
 * Camera frames never leave the browser: only derived numbers are sent to the
 * backend. Callers should fall back to "mode démo sans caméra" when this throws
 * (offline demo).
 */
import type { Landmark } from './gesture'

const TASKS_VISION_VERSION = '1.1.1'
const TASKS_VISION_BASE = `https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@${TASKS_VISION_VERSION}`
const WASM_URL = `${TASKS_VISION_BASE}/wasm`
const MODEL_URL =
  'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task'

export type HandLandmarkerLike = {
  detectForVideo(video: HTMLVideoElement, timestamp: number): { landmarks?: Landmark[][] }
  close(): void
}

/** MediaPipe hand skeleton: index pairs into the 21-landmark array. */
export const HAND_CONNECTIONS: ReadonlyArray<readonly [number, number]> = [
  [0, 1], [1, 2], [2, 3], [3, 4], // thumb
  [0, 5], [5, 6], [6, 7], [7, 8], // index
  [5, 9], [9, 10], [10, 11], [11, 12], // middle
  [9, 13], [13, 14], [14, 15], [15, 16], // ring
  [13, 17], [17, 18], [18, 19], [19, 20], // pinky
  [0, 17], // palm base
]

let cached: HandLandmarkerLike | null = null

async function createLandmarker(
  vision: {
    HandLandmarker: {
      createFromOptions(fileset: unknown, options: unknown): Promise<HandLandmarkerLike>
    }
  },
  fileset: unknown,
  delegate: 'GPU' | 'CPU',
): Promise<HandLandmarkerLike> {
  return vision.HandLandmarker.createFromOptions(fileset, {
    baseOptions: { modelAssetPath: MODEL_URL, delegate },
    runningMode: 'VIDEO',
    numHands: 1,
  })
}

// WebGL/GPU is faster but unavailable on many machines and headless contexts
// ("emscripten_webgl_create_context() returned error 0", "StartGraph failed").
// CPU is universally reliable for single-hand landmark detection, so it is the
// default; set to 'GPU' to opt into the WebGL delegate when you know it exists.
const DELEGATE: 'GPU' | 'CPU' = 'CPU'

export async function loadHandLandmarker(): Promise<HandLandmarkerLike> {
  if (cached) return cached

  // Runtime CDN import — @vite-ignore keeps Vite from statically resolving it.
  const vision = (await import(/* @vite-ignore */ `${TASKS_VISION_BASE}/vision_bundle.mjs`)) as {
    FilesetResolver: { forVisionTasks(path: string): Promise<unknown> }
    HandLandmarker: {
      createFromOptions(fileset: unknown, options: unknown): Promise<HandLandmarkerLike>
    }
  }

  const fileset = await vision.FilesetResolver.forVisionTasks(WASM_URL)
  try {
    cached = await createLandmarker(vision, fileset, DELEGATE)
  } catch (err) {
    if (DELEGATE === 'GPU') {
      cached = await createLandmarker(vision, fileset, 'CPU')
    } else {
      throw err
    }
  }
  return cached
}

export function closeHandLandmarker(): void {
  cached?.close()
  cached = null
}

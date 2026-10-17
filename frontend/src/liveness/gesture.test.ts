import { describe, expect, it } from 'vitest'

import {
  GestureDetector,
  analyze,
  handCenter,
  pinchRatio,
  type Landmark,
} from './gesture'

/** Synthetic hand: center is exactly (cx, cy); pinch ratio controlled directly. */
function hand(cx: number, cy: number, ratio = 1): Landmark[] {
  const lm: Landmark[] = Array.from({ length: 21 }, () => ({ x: cx, y: cy }))
  lm[0] = { x: cx, y: cy } // wrist
  lm[5] = { x: cx, y: cy } // index mcp
  lm[17] = { x: cx, y: cy } // pinky mcp → center = (cx, cy)
  lm[9] = { x: cx, y: cy + 0.1 } // middle mcp → hand size = 0.1
  const gap = ratio * 0.1
  lm[4] = { x: cx - gap / 2, y: cy } // thumb tip
  lm[8] = { x: cx + gap / 2, y: cy } // index tip
  return lm
}

function trajectory(gs: Array<[number, number]>, ratio = 1): Landmark[][] {
  return gs.map(([x, y]) => hand(x, y, ratio))
}

describe('handCenter / pinchRatio', () => {
  it('recovers the synthetic center', () => {
    const center = handCenter(hand(0.4, 0.6))
    expect(center.x).toBeCloseTo(0.4, 6)
    expect(center.y).toBeCloseTo(0.6, 6)
  })

  it('reads back the requested pinch ratio', () => {
    expect(pinchRatio(hand(0.5, 0.5, 0.3))).toBeCloseTo(0.3, 5)
  })
})

describe('analyze — left_to_right', () => {
  it('matches a rightward sweep', () => {
    const frames = trajectory([
      [0.2, 0.5], [0.3, 0.5], [0.4, 0.5], [0.5, 0.5],
      [0.6, 0.5], [0.7, 0.5], [0.8, 0.5], [0.8, 0.5],
      [0.8, 0.5], [0.8, 0.5], [0.8, 0.5], [0.8, 0.5],
    ])
    const obs = analyze('left_to_right', frames)
    expect(obs.gesture_matched).toBe(true)
    expect(obs.movement_score).toBeGreaterThanOrEqual(0.15)
    expect(obs.directions).toContain('right')
  })

  it('rejects a leftward sweep', () => {
    const frames = trajectory([
      [0.8, 0.5], [0.7, 0.5], [0.6, 0.5], [0.5, 0.5],
      [0.4, 0.5], [0.3, 0.5], [0.2, 0.5], [0.2, 0.5],
      [0.2, 0.5], [0.2, 0.5], [0.2, 0.5], [0.2, 0.5],
    ])
    expect(analyze('left_to_right', frames).gesture_matched).toBe(false)
  })

  it('rejects a too-short sweep', () => {
    const frames = trajectory([
      [0.4, 0.5], [0.42, 0.5], [0.44, 0.5], [0.45, 0.5],
      [0.46, 0.5], [0.47, 0.5], [0.48, 0.5], [0.49, 0.5],
      [0.5, 0.5], [0.51, 0.5], [0.52, 0.5], [0.53, 0.5],
    ])
    expect(analyze('left_to_right', frames).gesture_matched).toBe(false)
  })
})

describe('analyze — raise_hand', () => {
  it('matches an upward motion', () => {
    const frames = trajectory([
      [0.5, 0.8], [0.5, 0.75], [0.5, 0.7], [0.5, 0.6],
      [0.5, 0.5], [0.5, 0.4], [0.5, 0.3], [0.5, 0.2],
      [0.5, 0.2], [0.5, 0.2],
    ])
    const obs = analyze('raise_hand', frames)
    expect(obs.gesture_matched).toBe(true)
    expect(obs.directions).toContain('up')
  })

  it('rejects a horizontal motion', () => {
    const frames = trajectory([
      [0.2, 0.5], [0.3, 0.5], [0.4, 0.5], [0.5, 0.5],
      [0.6, 0.5], [0.7, 0.5], [0.8, 0.5], [0.8, 0.5],
    ])
    expect(analyze('raise_hand', frames).gesture_matched).toBe(false)
  })
})

describe('analyze — pinch', () => {
  it('matches two open/close cycles', () => {
    const ratios = [0.2, 1, 0.2, 1, 0.2, 1, 0.2, 1, 1, 1]
    const frames = ratios.map((r) => hand(0.5, 0.5, r))
    const obs = analyze('pinch', frames)
    expect(obs.gesture_matched).toBe(true)
    expect(obs.movement_score).toBeGreaterThanOrEqual(0.02)
  })

  it('rejects a single pinch', () => {
    const ratios = [0.2, 1, 1, 1, 1, 1, 1, 1]
    const frames = ratios.map((r) => hand(0.5, 0.5, r))
    expect(analyze('pinch', frames).gesture_matched).toBe(false)
  })
})

describe('analyze — wave', () => {
  it('matches at least two reversals', () => {
    const frames = trajectory([
      [0.2, 0.5], [0.5, 0.5], [0.8, 0.5], [0.5, 0.5],
      [0.2, 0.5], [0.5, 0.5], [0.8, 0.5], [0.5, 0.5],
      [0.2, 0.5], [0.5, 0.5], [0.8, 0.5], [0.5, 0.5],
    ])
    const obs = analyze('wave', frames)
    expect(obs.gesture_matched).toBe(true)
    expect(obs.movement_score).toBeGreaterThanOrEqual(0.18)
  })

  it('rejects in-place jitter', () => {
    const frames = trajectory([
      [0.5, 0.5], [0.5, 0.5], [0.5, 0.5], [0.5, 0.5],
      [0.5, 0.5], [0.5, 0.5], [0.5, 0.5], [0.5, 0.5],
      [0.5, 0.5], [0.5, 0.5], [0.5, 0.5], [0.5, 0.5],
    ])
    expect(analyze('wave', frames).gesture_matched).toBe(false)
  })
})

describe('GestureDetector', () => {
  it('accumulates frames and evaluates', () => {
    const detector = new GestureDetector('raise_hand')
    for (const y of [0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.2]) {
      detector.addFrame(hand(0.5, y))
    }
    expect(detector.frameCount).toBe(8)
    expect(detector.evaluate().gesture_matched).toBe(true)
  })

  it('ignores malformed frames and can reset', () => {
    const detector = new GestureDetector('pinch')
    detector.addFrame([{ x: 0.5, y: 0.5 }])
    expect(detector.frameCount).toBe(0)
    detector.addFrame(hand(0.5, 0.5))
    expect(detector.frameCount).toBe(1)
    detector.reset()
    expect(detector.frameCount).toBe(0)
  })

  it('reports an empty observation when no frames arrived', () => {
    const obs = new GestureDetector('left_to_right').evaluate()
    expect(obs.hand_frames).toBe(0)
    expect(obs.gesture_matched).toBe(false)
    expect(obs.pinch_ratio).toBeNull()
  })
})

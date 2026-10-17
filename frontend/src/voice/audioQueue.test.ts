import { beforeEach, describe, expect, it, vi } from 'vitest'

import { AudioQueue, type VoiceClip } from './audioQueue'

class FakeAudio {
  src: string
  onended: (() => void) | null = null
  onerror: (() => void) | null = null
  paused = false
  playCalls = 0

  constructor(src: string) {
    this.src = src
  }

  play(): Promise<void> {
    this.playCalls += 1
    return Promise.resolve()
  }

  pause(): void {
    this.paused = true
  }

  finish(): void {
    this.onended?.()
  }
}

function clip(sequence: number, audio_b64 = 'ID3fake'): VoiceClip {
  return { sequence, audio_b64, mime: 'audio/mpeg' }
}

function factory(created: FakeAudio[]) {
  return (src: string): HTMLAudioElement => {
    const audio = new FakeAudio(src)
    created.push(audio)
    return audio as unknown as HTMLAudioElement
  }
}

function flush(): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, 5))
}

beforeEach(() => {
  Object.assign(URL, {
    createObjectURL: vi.fn(() => 'blob:test'),
    revokeObjectURL: vi.fn(),
  })
})

describe('AudioQueue', () => {
  it('plays clips sequentially — the next starts only after the previous ends', async () => {
    const created: FakeAudio[] = []
    const queue = new AudioQueue(factory(created))

    queue.enqueue(clip(0))
    queue.enqueue(clip(1))
    await flush()

    // Only the first clip is playing; the second is still queued.
    expect(created).toHaveLength(1)
    expect(created[0].playCalls).toBe(1)

    created[0].finish()
    await flush()

    expect(created).toHaveLength(2)
    expect(created[1].playCalls).toBe(1)
  })

  it('decodes base64 into an audio blob', async () => {
    const created: FakeAudio[] = []
    const queue = new AudioQueue(factory(created))

    queue.enqueue(clip(0, btoa('hello')))
    await flush()

    expect(URL.createObjectURL).toHaveBeenCalledTimes(1)
    const [blobArg] = (URL.createObjectURL as unknown as { mock: { calls: unknown[][] } }).mock.calls[0]
    expect(blobArg).toBeInstanceOf(Blob)
    expect((blobArg as Blob).type).toBe('audio/mpeg')
    created[0]?.finish()
  })

  it('ignores clips without audio data', async () => {
    const created: FakeAudio[] = []
    const queue = new AudioQueue(factory(created))

    queue.enqueue(clip(0, ''))
    await flush()

    expect(created).toHaveLength(0)
  })

  it('stop pauses the current clip and clears the pending queue', async () => {
    const created: FakeAudio[] = []
    const queue = new AudioQueue(factory(created))

    queue.enqueue(clip(0))
    queue.enqueue(clip(1))
    await flush()
    queue.stop()

    expect(created[0].paused).toBe(true)
    await flush()
    // The queued second clip is never played after stop().
    expect(created).toHaveLength(1)
  })
})

/**
 * AudioQueue — sequential playback of base64 mp3 narration clips.
 *
 * Guardian emits `voice_audio` SSE events as they are synthesized. Clips must
 * never overlap, so this queue plays them strictly one after another. Any
 * decode/playback failure is swallowed: captions remain the source of truth and
 * the demo is never interrupted.
 */

export type VoiceClip = {
  sequence: number
  audio_b64: string
  mime: string
}

type AudioFactory = (src: string) => HTMLAudioElement

export class AudioQueue {
  private readonly queue: VoiceClip[] = []
  private readonly createAudio: AudioFactory
  private current: HTMLAudioElement | null = null
  private currentUrl: string | null = null
  private resolveCurrent: (() => void) | null = null
  private playing = false

  constructor(createAudio?: AudioFactory) {
    this.createAudio = createAudio ?? ((src) => new Audio(src))
  }

  enqueue(clip: VoiceClip): void {
    if (!clip.audio_b64) return
    this.queue.push(clip)
    void this.playNext()
  }

  stop(): void {
    this.queue.length = 0
    const resolve = this.resolveCurrent
    this.resolveCurrent = null
    if (this.current) {
      this.current.onended = null
      this.current.onerror = null
      this.current.pause()
      this.current = null
    }
    if (this.currentUrl) {
      URL.revokeObjectURL(this.currentUrl)
      this.currentUrl = null
    }
    this.playing = false
    resolve?.()
  }

  private async playNext(): Promise<void> {
    if (this.playing) return
    const clip = this.queue.shift()
    if (!clip) return
    this.playing = true

    let url: string | null = null
    try {
      const bytes = Uint8Array.from(atob(clip.audio_b64), (c) => c.charCodeAt(0))
      const blob = new Blob([bytes], { type: clip.mime || 'audio/mpeg' })
      url = URL.createObjectURL(blob)
      this.currentUrl = url
      const audio = this.createAudio(url)
      this.current = audio

      await new Promise<void>((resolve) => {
        this.resolveCurrent = () => {
          this.resolveCurrent = null
          resolve()
        }
        audio.onended = () => this.resolveCurrent?.()
        audio.onerror = () => this.resolveCurrent?.()
        const played = audio.play()
        if (played && typeof played.catch === 'function') {
          played.catch(() => this.resolveCurrent?.())
        }
      })
    } catch {
      // Audio unavailable — captions remain. Never surface to the demo.
    } finally {
      if (url) URL.revokeObjectURL(url)
      this.current = null
      this.currentUrl = null
      this.playing = false
      if (this.queue.length > 0) void this.playNext()
    }
  }
}

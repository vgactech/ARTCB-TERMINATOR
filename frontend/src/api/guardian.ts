export type GuardianStep = {
  step_id: string
  description: string
  status: 'PASS' | 'FAIL' | 'NOT_TESTED' | 'SKIP'
  details: Record<string, unknown>
}

export type ReplayResult = {
  level: string
  verdict: 'PASS' | 'FAIL' | 'IN_DOUBT'
  events_replayed: number
  mismatches: Array<Record<string, unknown>>
  limits: string[]
}

export type SimulationReport = {
  session_id: string
  run_id: string
  steps: GuardianStep[]
  blocking: {
    decision: string
    evidence_id: string
    guardian_event_id: string
    tool_name: string
    reason: string
    tool_was_executed: boolean
  } | null
  replay_r0_intact: ReplayResult | null
  replay_r1_intact: ReplayResult | null
  replay_r0_tampered: ReplayResult | null
  overall_verdict: 'GO' | 'NO_GO'
  protected: boolean
  tampering_detected: boolean
}

const apiBaseUrl = import.meta.env.VITE_API_URL?.replace(/\/$/, '') ?? ''

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${apiBaseUrl}${path}`, init)
  } catch {
    throw new Error('Guardian API is offline. Start the backend on port 8000 and try again.')
  }

  if (!response.ok) {
    let detail = `Guardian API returned HTTP ${response.status}.`
    try {
      const payload = await response.json() as { detail?: string }
      if (payload.detail) detail = payload.detail
    } catch {
      // Retain the status-based message when the response is not JSON.
    }
    throw new Error(detail)
  }

  return response.json() as Promise<T>
}

export function checkGuardianHealth() {
  return request<{ status: string; service: string; engine: string }>('/api/health')
}

export function runGuardianSimulation() {
  return request<SimulationReport>('/api/simulation/run', { method: 'POST' })
}

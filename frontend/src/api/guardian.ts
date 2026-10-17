export type KycStreamEvent = {
  _type: string
  [key: string]: unknown
}

export type KycResult = {
  verdict: 'APPROVED' | 'REJECTED' | 'PENDING'
  score: number
  attacks_blocked: number
  chain_intact: boolean
  liveness?: 'PASS' | 'FAIL' | 'SIMULATED' | 'SKIPPED'
  human_proven?: boolean
  session_id: string
  run_id: string
  timestamp: string
  first_name: string
  last_name: string
  doc_id: string
  reason: string
}

export type VoiceScriptEvent = {
  role: string
  text: string
  sequence: number
}

export type VoiceAudioEvent = {
  role: string
  sequence: number
  audio_b64: string
  mime: string
  speed?: number
}

export type VoiceStatus = {
  voice_enabled: boolean
  api_key_configured: boolean
  voices: Record<string, string>
}

export type LivenessGesture = {
  id: string
  instruction_fr: string
  instruction_en: string
  min_frames: number
}

export type LivenessStatus = {
  enabled: boolean
  ttl_seconds: number
  data_source: string
  gestures: LivenessGesture[]
}

export type LivenessChallenge = {
  challenge_id: string
  gesture: string
  nonce: string
  instruction_fr: string
  instruction_en: string
  expires_at: number
  ttl_seconds: number
  simulated: boolean
  data_source: string
}

export type LivenessObservation = {
  gesture: string
  hand_frames: number
  movement_score: number
  directions: string[]
  pinch_ratio: number | null
  gesture_matched: boolean
  duration_ms: number
  simulated?: boolean
}

export type LivenessVerdict = 'PASS' | 'FAIL' | 'SIMULATED'

export type LivenessResult = {
  liveness: LivenessVerdict
  reason: string
  human_proven: boolean
  gesture: string
  evidence_id: string | null
  guardian_event_id: string | null
  data_source: string
}

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

export type PolicyScenario = {
  id: string
  name: string
  description: string
  risk: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
}

export type GuardianEvent = {
  event_id: string
  event_phase: 'INTENT' | 'TERMINAL'
  sequence_no: number
  decision: 'ALLOW' | 'BLOCK' | 'REDACT' | 'ESCALATE'
  decision_reason: string
  execution_status: string
  tool_name: string
  event_hash: string
  previous_event_hash: string
  hash_valid: boolean
  parent_valid: boolean
}

export type PolicyScenarioResult = {
  scenario: PolicyScenario
  session_id: string
  run_id: string
  decision: GuardianEvent['decision']
  reason: string
  tool_name: string
  execution_status: string
  tool_was_executed: boolean
  evidence_id: string | null
  guardian_event_id: string
  intent_id: string
  agents: Array<{
    index: number
    id: string
    role: 'orchestrator' | 'source' | 'propagator' | 'defender'
    status: 'COMPLETED'
    artifact_id: string
    events: number
  }>
  distinct_agent_count: number
  request: {
    request_id: string
    content_hash: string
  }
  propagation: {
    propagation_id: string
    payload_id: string
    payload_content_hash: string
    from_agent: string
    via_agent: string
    to_agent: string
  }
  events: GuardianEvent[]
  chain_verification: {
    level: string
    verdict: 'PASS' | 'FAIL'
    events_replayed: number
    mismatches: string[]
  }
  tamper_verification: {
    level: string
    verdict: 'PASS' | 'FAIL'
    events_replayed: number
    mismatches: Array<{
      event_id: string
      field: string
      expected: string
      actual: string
    }>
    original_archive_unchanged: boolean
  }
}

// Shared API base. Empty string means same-origin (Vite dev proxy / nginx).
// Set VITE_API_URL to target a backend on another origin, e.g. http://127.0.0.1:8002.
export const apiBaseUrl = import.meta.env.VITE_API_URL?.replace(/\/$/, '') ?? ''

/** Prefix a path with the configured API base (works same-origin and cross-origin). */
export function apiUrl(path: string): string {
  return `${apiBaseUrl}${path}`
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(apiUrl(path), init)
  } catch {
    throw new Error(
      'Guardian API is offline. Start the backend (./start_guardian.sh, default port 8002) and try again.',
    )
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

export function listGuardianScenarios() {
  return request<PolicyScenario[]>('/api/scenarios')
}

export function runGuardianScenario(scenarioId: string) {
  return request<PolicyScenarioResult>(`/api/scenarios/${scenarioId}/run`, { method: 'POST' })
}

export function fetchLivenessStatus() {
  return request<LivenessStatus>('/api/liveness/status')
}

export function createLivenessChallenge() {
  return request<LivenessChallenge>('/api/liveness/challenge', { method: 'POST' })
}

export function verifyLiveness(body: LivenessObservation & { challenge_id: string; nonce: string }) {
  return request<LivenessResult>('/api/liveness/verify', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}

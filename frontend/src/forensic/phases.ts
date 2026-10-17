/**
 * ARTCB TERMINATOR FORENSIC — Audio Alert System
 *
 * Pre-defined audio phases triggered by confirmed Guardian events.
 * Audio is asynchronous and NEVER blocks a Guardian decision.
 * If synthesis fails, the forensic process continues unaffected.
 *
 * Phase progression is driven by real API events, not animations.
 */

import { apiUrl } from '../api/guardian'

export type ForensicPhase =
  | 'idle'
  | 'scenario_start'
  | 'suspicious_activity'
  | 'attack_detected'
  | 'action_blocked'
  | 'containment'
  | 'evidence_generated'
  | 'chain_verified'
  | 'tamper_detected'
  | 'resolution_complete'
  | 'verification_incomplete'

export interface PhaseConfig {
  phase: ForensicPhase
  label: string
  shortLabel: string
  /** Detection % — what fraction of the attack chain is detected */
  detectionPct: number
  /** Block % — what fraction has been blocked/contained */
  blockPct: number
  /** Resolution % — verified and closed */
  resolutionPct: number
  /** Pre-recorded alert text (spoken by ElevenLabs or displayed as caption) */
  alertText: string
  /** Short strategic summary shown during critical moments */
  strategicSummary: string
  color: 'neutral' | 'yellow' | 'orange' | 'red' | 'green' | 'blue'
}

export const PHASE_CONFIGS: Record<ForensicPhase, PhaseConfig> = {
  idle: {
    phase: 'idle',
    label: 'System Ready',
    shortLabel: 'READY',
    detectionPct: 0,
    blockPct: 0,
    resolutionPct: 0,
    alertText: 'ARTCB TERMINATOR FORENSIC — Guardian armed and ready.',
    strategicSummary: 'Awaiting scenario.',
    color: 'neutral',
  },
  scenario_start: {
    phase: 'scenario_start',
    label: 'Scenario Initiated',
    shortLabel: 'INIT',
    detectionPct: 10,
    blockPct: 0,
    resolutionPct: 0,
    alertText: 'Guardian scenario initiated. Four agents online.',
    strategicSummary: 'Request received. Agents activating.',
    color: 'blue',
  },
  suspicious_activity: {
    phase: 'suspicious_activity',
    label: 'Suspicious Activity Detected',
    shortLabel: 'ALERT',
    detectionPct: 45,
    blockPct: 0,
    resolutionPct: 0,
    alertText: 'Alert — suspicious activity detected. Guardian evaluating.',
    strategicSummary: 'Suspicious activity. Awaiting policy decision.',
    color: 'yellow',
  },
  attack_detected: {
    phase: 'attack_detected',
    label: 'Attack Detected',
    shortLabel: 'ATTACK',
    detectionPct: 85,
    blockPct: 20,
    resolutionPct: 0,
    alertText: 'Alert — attack detected. Guardian intercepting tool call.',
    strategicSummary: 'Attack in progress. Interception active.',
    color: 'orange',
  },
  action_blocked: {
    phase: 'action_blocked',
    label: 'Action Blocked by Policy',
    shortLabel: 'BLOCKED',
    detectionPct: 100,
    blockPct: 80,
    resolutionPct: 30,
    alertText: 'Action blocked by Guardian security policy. Tool not executed.',
    strategicSummary: 'BLOCK confirmed. Evidence ID generated.',
    color: 'red',
  },
  containment: {
    phase: 'containment',
    label: 'Containment Active',
    shortLabel: 'CONTAIN',
    detectionPct: 100,
    blockPct: 95,
    resolutionPct: 50,
    alertText: 'Containment in progress. No tool executed.',
    strategicSummary: 'Contained. Verifying cryptographic chain.',
    color: 'orange',
  },
  evidence_generated: {
    phase: 'evidence_generated',
    label: 'Evidence Generated',
    shortLabel: 'EVIDENCE',
    detectionPct: 100,
    blockPct: 100,
    resolutionPct: 65,
    alertText: 'Cryptographic evidence generated. Chain integrity confirmed.',
    strategicSummary: 'Evidence ID present. Chain R0 in progress.',
    color: 'blue',
  },
  chain_verified: {
    phase: 'chain_verified',
    label: 'Chain Verified — R0 PASS',
    shortLabel: 'VERIFIED',
    detectionPct: 100,
    blockPct: 100,
    resolutionPct: 90,
    alertText: 'Audit chain verified. R0 integrity PASS.',
    strategicSummary: 'R0 PASS. Tamper simulation confirmed detection.',
    color: 'green',
  },
  tamper_detected: {
    phase: 'tamper_detected',
    label: 'Tamper Attempt Detected',
    shortLabel: 'TAMPER',
    detectionPct: 100,
    blockPct: 100,
    resolutionPct: 80,
    alertText: 'Tamper simulation — alteration detected by Guardian. Archive intact.',
    strategicSummary: 'Tamper detected. Original archive unchanged.',
    color: 'red',
  },
  resolution_complete: {
    phase: 'resolution_complete',
    label: 'Incident Closed',
    shortLabel: 'RESOLVED',
    detectionPct: 100,
    blockPct: 100,
    resolutionPct: 100,
    alertText: 'Incident closed after verification. Guardian forensic record complete.',
    strategicSummary: 'RESOLVED. Full forensic trail available.',
    color: 'green',
  },
  verification_incomplete: {
    phase: 'verification_incomplete',
    label: 'Verification Incomplete',
    shortLabel: 'INCOMPLETE',
    detectionPct: 100,
    blockPct: 80,
    resolutionPct: 40,
    alertText: 'Verification incomplete. Some telemetry unavailable.',
    strategicSummary: 'Partial verification. Review forensic log.',
    color: 'yellow',
  },
}

/**
 * Determine the forensic phase from a live Guardian API result.
 * Driven by real event data — not by animation timers.
 */
export function phaseFromResult(result: {
  decision?: string
  tool_was_executed?: boolean
  evidence_id?: string | null
  chain_verification?: { verdict: string }
  tamper_verification?: { verdict: string; original_archive_unchanged?: boolean }
} | null): ForensicPhase {
  if (!result) return 'idle'

  const decision = result.decision
  const chainPass = result.chain_verification?.verdict === 'PASS'
  const tamperFail = result.tamper_verification?.verdict === 'FAIL'
  const archiveUnchanged = result.tamper_verification?.original_archive_unchanged

  if (decision === 'ALLOW' && result.tool_was_executed) {
    return chainPass ? 'resolution_complete' : 'verification_incomplete'
  }

  if (decision === 'BLOCK' || decision === 'ESCALATE') {
    if (chainPass && tamperFail && archiveUnchanged) return 'resolution_complete'
    if (chainPass && result.evidence_id) return 'chain_verified'
    if (result.evidence_id) return 'evidence_generated'
    return 'action_blocked'
  }

  return 'suspicious_activity'
}

/**
 * Animate phase progression during a live run.
 * Returns the intermediate phase based on agent index (0-3).
 */
export function phaseFromAgentIndex(
  agentIndex: number,
  decision?: string,
): ForensicPhase {
  if (agentIndex < 0) return 'idle'
  if (agentIndex === 0) return 'scenario_start'
  if (agentIndex === 1) {
    return decision === 'BLOCK' ? 'attack_detected' : 'suspicious_activity'
  }
  if (agentIndex === 2) return 'containment'
  if (agentIndex >= 3) return 'evidence_generated'
  return 'suspicious_activity'
}

/** Play alert text via ElevenLabs SSE or display as caption (never blocks Guardian). */
export async function speakPhaseAlert(
  alertText: string,
  voice = true,
): Promise<void> {
  if (!voice) return
  // Non-blocking: fire and forget. Audio failure never affects forensic logic.
  try {
    const resp = await fetch(apiUrl('/api/llm-attack/stream?voice=true&speed=1.1'), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt: alertText }),
      signal: AbortSignal.timeout(3000),
    })
    if (!resp.ok) return
    // SSE voice stream handled by the existing VoiceCommentary system
  } catch {
    // Audio unavailable — forensic process unaffected
  }
}

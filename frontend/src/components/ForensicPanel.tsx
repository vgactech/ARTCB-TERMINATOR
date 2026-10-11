/**
 * ForensicPanel — displays real-time forensic indicators driven by phases.ts
 *
 * Shows:
 *   - Detection %, Block %, Resolution % (progress bars)
 *   - Current phase label + color
 *   - Alert text (narration caption)
 *   - Strategic summary
 *   - ARTCB MCP bridge status (live)
 */

import { useEffect, useState } from 'react'
import { ShieldAlert, Lock, CheckCircle, Zap } from 'lucide-react'
import { PHASE_CONFIGS } from '../forensic/phases'
import type { ForensicPhase } from '../forensic/phases'
import type { PolicyScenarioResult } from '../api/guardian'

interface ForensicPanelProps {
  phase: ForensicPhase
  result: PolicyScenarioResult | null
  running: boolean
}

interface ArtcbStatus {
  available: boolean
  api_url?: string
  server_name?: string
  server_version?: string
  tool_count?: number
  error?: string
}

const colorMap: Record<string, string> = {
  neutral: 'text-slate-400',
  blue:    'text-cyan-300',
  yellow:  'text-yellow-300',
  orange:  'text-orange-300',
  red:     'text-rose-400',
  green:   'text-emerald-400',
}

const barColorMap: Record<string, string> = {
  neutral: 'bg-slate-500',
  blue:    'bg-cyan-400',
  yellow:  'bg-yellow-400',
  orange:  'bg-orange-400',
  red:     'bg-rose-500',
  green:   'bg-emerald-400',
}

interface BarProps {
  label: string
  pct: number
  color: string
  icon: React.ReactNode
}

function MetricBar({ label, pct, color, icon }: BarProps) {
  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between text-xs">
        <span className="flex items-center gap-1.5 text-slate-400">
          {icon}
          {label}
        </span>
        <span className="font-mono font-semibold text-white">{pct}%</span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-white/8">
        <div
          className={`h-full rounded-full transition-all duration-700 ${barColorMap[color] ?? 'bg-slate-500'}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}

export function ForensicPanel({ phase, result, running }: ForensicPanelProps) {
  const config = PHASE_CONFIGS[phase]
  const [artcbStatus, setArtcbStatus] = useState<ArtcbStatus | null>(null)
  const [artcbChecked, setArtcbChecked] = useState(false)

  // Fetch ARTCB MCP bridge status once on mount
  useEffect(() => {
    fetch('/api/artcb/status')
      .then((r) => r.ok ? r.json() : Promise.reject(r.status))
      .then((data: ArtcbStatus) => setArtcbStatus(data))
      .catch(() => setArtcbStatus({ available: false, error: 'unreachable' }))
      .finally(() => setArtcbChecked(true))
  }, [])

  const phaseColor = colorMap[config.color] ?? 'text-slate-400'

  return (
    <article className="rounded-2xl border border-white/8 bg-slate-950/55 p-5 space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold text-white">Forensic Indicators</p>
          <p className="mt-0.5 text-xs text-slate-400">Real-time phase analysis</p>
        </div>
        <span className={`font-mono text-[11px] font-bold tracking-widest ${phaseColor}`}>
          {config.shortLabel}
        </span>
      </div>

      {/* Three metrics */}
      <div className="space-y-3">
        <MetricBar
          label="Detection"
          pct={config.detectionPct}
          color={config.color}
          icon={<ShieldAlert size={12} aria-hidden="true" />}
        />
        <MetricBar
          label="Blocked"
          pct={config.blockPct}
          color={config.color}
          icon={<Lock size={12} aria-hidden="true" />}
        />
        <MetricBar
          label="Resolution"
          pct={config.resolutionPct}
          color={config.color}
          icon={<CheckCircle size={12} aria-hidden="true" />}
        />
      </div>

      {/* Alert text / caption */}
      {(running || result) && (
        <div className="rounded-xl border border-white/6 bg-black/30 px-4 py-3">
          <p className={`text-xs font-medium leading-5 ${phaseColor}`}>
            {config.alertText}
          </p>
          {config.strategicSummary && (
            <p className="mt-1 text-[11px] text-slate-400">{config.strategicSummary}</p>
          )}
        </div>
      )}

      {/* ARTCB MCP status */}
      {artcbChecked && (
        <div className="flex items-center justify-between rounded-lg border border-white/6 bg-black/20 px-3 py-2">
          <span className="flex items-center gap-1.5 text-[11px] text-slate-400">
            <Zap size={11} aria-hidden="true" />
            ARTCB MCP Bridge
          </span>
          {artcbStatus?.available ? (
            <span className="font-mono text-[10px] font-bold text-emerald-400">
              ONLINE · {artcbStatus.tool_count ?? 0} tools
            </span>
          ) : (
            <span className="font-mono text-[10px] font-bold text-slate-400">
              OFFLINE
            </span>
          )}
        </div>
      )}

      {/* Decision badge (when result is available) */}
      {result && (
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400">Guardian decision:</span>
          <span
            className={`rounded-md px-2 py-0.5 font-mono text-[11px] font-bold ${
              result.decision === 'ALLOW'
                ? 'bg-emerald-400/10 text-emerald-300'
                : result.decision === 'BLOCK'
                ? 'bg-rose-500/10 text-rose-400'
                : 'bg-orange-400/10 text-orange-300'
            }`}
          >
            {result.decision}
          </span>
        </div>
      )}
    </article>
  )
}

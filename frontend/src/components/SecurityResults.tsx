import { Ban, Check, Fingerprint, ShieldCheck } from 'lucide-react'
import type { PolicyScenarioResult } from '../api/guardian'

type SecurityResultsProps = {
  result: PolicyScenarioResult
}

export function SecurityResults({ result }: SecurityResultsProps) {
  const results = [
    {
      label: 'Policy decision',
      value: result.decision,
      icon: Ban,
      className: result.decision === 'ALLOW'
        ? 'text-emerald-300 bg-emerald-400/8 border-emerald-400/20'
        : result.decision === 'ESCALATE'
          ? 'text-amber-300 bg-amber-400/8 border-amber-400/20'
          : 'text-rose-300 bg-rose-400/8 border-rose-400/20',
    },
    { label: 'Tool execution', value: result.execution_status.replace('_', ' '), icon: Check, className: 'text-emerald-300 bg-emerald-400/8 border-emerald-400/20' },
    { label: 'Evidence status', value: result.evidence_id ? 'CREATED' : 'NOT REQUIRED', icon: Fingerprint, className: 'text-cyan-300 bg-cyan-400/8 border-cyan-400/20' },
    { label: 'Chain verification', value: result.chain_verification.verdict, icon: ShieldCheck, className: 'text-violet-300 bg-violet-400/8 border-violet-400/20' },
  ]

  return (
    <section className="mt-6 rounded-2xl border border-white/8 bg-slate-950/55 p-6" aria-labelledby="security-results-heading">
      <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-end">
        <div>
          <h2 id="security-results-heading" className="text-sm font-semibold text-white">Real Guardian result</h2>
          <p className="mt-1 text-xs text-slate-500">Returned by the backend policy engine for {result.scenario.name}</p>
        </div>
        <span className="w-fit rounded-full border border-emerald-400/20 bg-emerald-400/7 px-3 py-1 font-mono text-[10px] font-semibold tracking-wider text-emerald-300">GUARDIAN VERIFIED</span>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {results.map((item) => {
          const Icon = item.icon
          return (
            <article key={item.label} className={`rounded-xl border p-4 ${item.className}`}>
              <Icon size={18} aria-hidden="true" />
              <p className="mt-4 text-[11px] text-slate-500">{item.label}</p>
              <p className="mt-1 font-mono text-xs font-bold tracking-wider">{item.value}</p>
            </article>
          )
        })}
      </div>

      <dl className="mt-5 grid gap-3 rounded-xl border border-white/6 bg-black/15 p-4 text-xs md:grid-cols-3">
        <div className="min-w-0">
          <dt className="text-slate-600">Evidence ID</dt>
          <dd className="mt-1 truncate font-mono text-slate-300" title={result.evidence_id ?? 'Not required'}>{result.evidence_id ?? 'Not required for this decision'}</dd>
        </div>
        <div className="min-w-0">
          <dt className="text-slate-600">Session ID</dt>
          <dd className="mt-1 truncate font-mono text-slate-300" title={result.session_id}>{result.session_id}</dd>
        </div>
        <div className="min-w-0">
          <dt className="text-slate-600">Run ID</dt>
          <dd className="mt-1 truncate font-mono text-slate-300" title={result.run_id}>{result.run_id}</dd>
        </div>
      </dl>
    </section>
  )
}

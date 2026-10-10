import { Ban, Check, Fingerprint, ShieldCheck } from 'lucide-react'

type SecurityResultsProps = {
  evidenceId: string
  sessionId: string
  runId: string
}

export function SecurityResults({ evidenceId, sessionId, runId }: SecurityResultsProps) {
  const results = [
    { label: 'Policy decision', value: 'BLOCK', icon: Ban, className: 'text-rose-300 bg-rose-400/8 border-rose-400/20' },
    { label: 'Tool execution', value: 'NOT EXECUTED', icon: Check, className: 'text-emerald-300 bg-emerald-400/8 border-emerald-400/20' },
    { label: 'Evidence status', value: 'CREATED', icon: Fingerprint, className: 'text-cyan-300 bg-cyan-400/8 border-cyan-400/20' },
    { label: 'Final verdict', value: 'PROTECTED', icon: ShieldCheck, className: 'text-violet-300 bg-violet-400/8 border-violet-400/20' },
  ]

  return (
    <section className="mt-6 rounded-2xl border border-white/8 bg-slate-950/55 p-6" aria-labelledby="security-results-heading">
      <div className="flex flex-col justify-between gap-2 sm:flex-row sm:items-end">
        <div>
          <h2 id="security-results-heading" className="text-sm font-semibold text-white">Security result</h2>
          <p className="mt-1 text-xs text-slate-500">Guardian enforcement and evidence summary</p>
        </div>
        <span className="w-fit rounded-full border border-emerald-400/20 bg-emerald-400/7 px-3 py-1 font-mono text-[10px] font-semibold tracking-wider text-emerald-300">INCIDENT CONTAINED</span>
      </div>

      <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {results.map((result) => {
          const Icon = result.icon
          return (
            <article key={result.label} className={`rounded-xl border p-4 ${result.className}`}>
              <Icon size={18} aria-hidden="true" />
              <p className="mt-4 text-[11px] text-slate-500">{result.label}</p>
              <p className="mt-1 font-mono text-xs font-bold tracking-wider">{result.value}</p>
            </article>
          )
        })}
      </div>

      <dl className="mt-5 grid gap-3 rounded-xl border border-white/6 bg-black/15 p-4 text-xs md:grid-cols-3">
        <div className="min-w-0">
          <dt className="text-slate-600">Evidence ID</dt>
          <dd className="mt-1 truncate font-mono text-slate-300" title={evidenceId}>{evidenceId}</dd>
        </div>
        <div className="min-w-0">
          <dt className="text-slate-600">Session ID</dt>
          <dd className="mt-1 truncate font-mono text-slate-300" title={sessionId}>{sessionId}</dd>
        </div>
        <div className="min-w-0">
          <dt className="text-slate-600">Run ID</dt>
          <dd className="mt-1 truncate font-mono text-slate-300" title={runId}>{runId}</dd>
        </div>
      </dl>
    </section>
  )
}

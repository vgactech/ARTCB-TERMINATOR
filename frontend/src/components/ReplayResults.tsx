import { CheckCircle2, FileSearch, ShieldAlert, XCircle } from 'lucide-react'

const verifiedReplays = [
  { level: 'R0', title: 'Chain integrity', detail: 'Hashes, sequence order, and parent links verified.', events: 1 },
  { level: 'R1', title: 'Decision evidence', detail: 'BLOCK decision linked to canonical Evidence ID.', events: 1 },
]

export function ReplayResults() {
  return (
    <section className="mt-6 grid gap-6 lg:grid-cols-[1.4fr_1fr]" aria-labelledby="replay-heading">
      <article className="rounded-2xl border border-white/8 bg-slate-950/55 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 id="replay-heading" className="text-sm font-semibold text-white">Incident replay</h2>
            <p className="mt-1 text-xs text-slate-500">Independent verification levels</p>
          </div>
          <FileSearch size={19} className="text-cyan-300" aria-hidden="true" />
        </div>

        <div className="mt-5 grid gap-3 sm:grid-cols-2">
          {verifiedReplays.map((replay) => (
            <article key={replay.level} className="rounded-xl border border-emerald-400/15 bg-emerald-400/[0.035] p-4">
              <div className="flex items-center justify-between">
                <span className="rounded-md bg-emerald-400/10 px-2 py-1 font-mono text-[10px] font-bold text-emerald-300">{replay.level}</span>
                <span className="flex items-center gap-1 font-mono text-[10px] font-semibold text-emerald-300"><CheckCircle2 size={13} /> PASS</span>
              </div>
              <h3 className="mt-4 text-sm font-semibold text-white">{replay.title}</h3>
              <p className="mt-2 text-xs leading-5 text-slate-500">{replay.detail}</p>
              <p className="mt-4 font-mono text-[10px] text-slate-600">{replay.events} EVENT REPLAYED · 0 MISMATCHES</p>
            </article>
          ))}
        </div>
      </article>

      <article className="relative overflow-hidden rounded-2xl border border-rose-400/20 bg-rose-950/10 p-6">
        <div className="absolute -top-10 -right-10 size-32 rounded-full bg-rose-500/8 blur-2xl" />
        <div className="relative flex items-center justify-between">
          <div>
            <p className="text-sm font-semibold text-white">Tamper challenge</p>
            <p className="mt-1 text-xs text-slate-500">Modified evidence replay</p>
          </div>
          <ShieldAlert size={20} className="text-rose-300" aria-hidden="true" />
        </div>
        <div className="relative mt-5 rounded-xl border border-rose-400/15 bg-rose-400/[0.035] p-4">
          <div className="flex items-center gap-2 font-mono text-xs font-bold tracking-wider text-rose-300">
            <XCircle size={16} /> REPLAY FAILED
          </div>
          <p className="mt-3 text-xs leading-5 text-slate-400">Guardian rejected the altered event because its recalculated hash no longer matched the evidence chain.</p>
          <div className="mt-4 flex items-center justify-between border-t border-rose-400/10 pt-4 font-mono text-[10px]">
            <span className="text-slate-600">EXPECTED RESULT</span>
            <span className="text-rose-300">TAMPERING DETECTED</span>
          </div>
        </div>
      </article>
    </section>
  )
}

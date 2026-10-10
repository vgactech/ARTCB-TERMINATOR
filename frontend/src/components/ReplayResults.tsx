import { CheckCircle2, FileSearch, ShieldAlert, XCircle } from 'lucide-react'
import type { PolicyScenarioResult } from '../api/guardian'

export function ReplayResults({ result }: { result: PolicyScenarioResult }) {
  const replay = result.chain_verification
  const tamper = result.tamper_verification
  return (
    <section className="mt-6 grid gap-6 lg:grid-cols-[1.4fr_1fr]" aria-labelledby="replay-heading">
      <article className="rounded-2xl border border-white/8 bg-slate-950/55 p-6">
        <div className="flex items-center justify-between"><div><h2 id="replay-heading" className="text-sm font-semibold text-white">Incident replay</h2><p className="mt-1 text-xs text-slate-500">Backend verification of the original event chain</p></div><FileSearch size={19} className="text-cyan-300" aria-hidden="true" /></div>
        <div className="mt-5 rounded-xl border border-emerald-400/15 bg-emerald-400/[0.035] p-4">
          <div className="flex items-center justify-between"><span className="rounded-md bg-emerald-400/10 px-2 py-1 font-mono text-[10px] font-bold text-emerald-300">{replay.level}</span><span className="flex items-center gap-1 font-mono text-[10px] font-semibold text-emerald-300"><CheckCircle2 size={13} /> {replay.verdict}</span></div>
          <h3 className="mt-4 text-sm font-semibold text-white">Hash and parent-link integrity</h3><p className="mt-2 text-xs leading-5 text-slate-500">Guardian recalculated every event hash and verified the chain from its genesis value.</p><p className="mt-4 font-mono text-[10px] text-slate-600">{replay.events_replayed} EVENTS REPLAYED · {replay.mismatches.length} MISMATCHES</p>
        </div>
      </article>
      <article className="relative overflow-hidden rounded-2xl border border-rose-400/20 bg-rose-950/10 p-6">
        <div className="relative flex items-center justify-between"><div><p className="text-sm font-semibold text-white">Tamper challenge</p><p className="mt-1 text-xs text-slate-500">Backend replay of a modified copy</p></div><ShieldAlert size={20} className="text-rose-300" aria-hidden="true" /></div>
        <div className="relative mt-5 rounded-xl border border-rose-400/15 bg-rose-400/[0.035] p-4">
          <div className="flex items-center gap-2 font-mono text-xs font-bold tracking-wider text-rose-300"><XCircle size={16} /> REPLAY {tamper.verdict}</div>
          <p className="mt-3 text-xs leading-5 text-slate-400">Guardian altered one copied hash and detected {tamper.mismatches.length} mismatch. The original archive remained {tamper.original_archive_unchanged ? 'unchanged' : 'modified'}.</p>
          <div className="mt-4 flex items-center justify-between border-t border-rose-400/10 pt-4 font-mono text-[10px]"><span className="text-slate-600">EXPECTED FAILURE</span><span className="text-rose-300">TAMPERING DETECTED</span></div>
        </div>
      </article>
    </section>
  )
}

import { ArrowRight, CheckCircle2, Fingerprint, Network } from 'lucide-react'
import type { PolicyScenarioResult } from '../api/guardian'

const labels = {
  orchestrator: 'Opened shared session',
  source: 'Constructed hashed request',
  propagator: 'Relayed request to Defender',
  defender: 'Applied Guardian policy',
}

export function OrchestrationProof({ result }: { result: PolicyScenarioResult }) {
  const requestRelayed = result.request.request_id === result.propagation.payload_id
  const hashPreserved = result.request.content_hash === result.propagation.payload_content_hash

  return (
    <section className="mt-6 overflow-hidden rounded-2xl border border-cyan-400/20 bg-cyan-950/[0.08]" aria-labelledby="orchestration-proof-heading">
      <div className="flex flex-col justify-between gap-3 border-b border-cyan-400/10 bg-cyan-400/[0.035] px-6 py-5 sm:flex-row sm:items-center">
        <div>
          <div className="flex items-center gap-2 text-cyan-300"><Network size={18} aria-hidden="true" /><h2 id="orchestration-proof-heading" className="text-sm font-semibold">Verified four-agent backend execution</h2></div>
          <p className="mt-1 text-xs text-slate-500">These identities and artifacts were returned by the API for this run.</p>
        </div>
        <span className="w-fit rounded-full border border-cyan-400/20 bg-cyan-400/8 px-3 py-1 font-mono text-[10px] font-bold text-cyan-300">{result.distinct_agent_count} DISTINCT INSTANCES</span>
      </div>

      <div className="grid gap-0 lg:grid-cols-4">
        {result.agents.map((agent, index) => (
          <div key={agent.id} className="relative border-b border-white/6 p-5 last:border-b-0 lg:border-r lg:border-b-0 lg:last:border-r-0">
            <div className="flex items-center justify-between">
              <span className="flex size-8 items-center justify-center rounded-lg bg-cyan-400/10 font-mono text-xs font-bold text-cyan-300">{index + 1}</span>
              <span className="flex items-center gap-1 font-mono text-[9px] font-bold text-emerald-300"><CheckCircle2 size={12} /> {agent.status}</span>
            </div>
            <p className="mt-4 text-sm font-semibold capitalize text-white">{agent.role}</p>
            <p className="mt-1 text-xs text-slate-500">{labels[agent.role]}</p>
            <p className="mt-4 break-all font-mono text-[10px] leading-4 text-slate-400">{agent.id}</p>
            <p className="mt-2 truncate font-mono text-[9px] text-slate-600" title={agent.artifact_id}>Artifact: {agent.artifact_id}</p>
            {index < result.agents.length - 1 && <ArrowRight className="absolute -right-2.5 top-1/2 z-10 hidden text-cyan-500 lg:block" size={18} aria-hidden="true" />}
          </div>
        ))}
      </div>

      <div className="grid gap-3 border-t border-cyan-400/10 p-5 md:grid-cols-3">
        <div className="rounded-xl border border-white/6 bg-black/15 p-4"><p className="text-[10px] uppercase tracking-wider text-slate-600">Request ID</p><p className="mt-2 truncate font-mono text-xs text-slate-300" title={result.request.request_id}>{result.request.request_id}</p></div>
        <div className="rounded-xl border border-white/6 bg-black/15 p-4"><p className="text-[10px] uppercase tracking-wider text-slate-600">Propagation ID</p><p className="mt-2 truncate font-mono text-xs text-slate-300" title={result.propagation.propagation_id}>{result.propagation.propagation_id}</p></div>
        <div className="rounded-xl border border-emerald-400/15 bg-emerald-400/[0.035] p-4"><p className="flex items-center gap-1 text-[10px] uppercase tracking-wider text-emerald-300"><Fingerprint size={12} /> Causal integrity</p><p className="mt-2 font-mono text-xs font-bold text-emerald-300">{requestRelayed && hashPreserved ? 'REQUEST + HASH MATCH' : 'MISMATCH DETECTED'}</p></div>
      </div>
    </section>
  )
}

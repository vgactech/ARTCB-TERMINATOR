import { Bot, RadioTower, Route, Shield } from 'lucide-react'

const agents = [
  { id: 'A', name: 'Orchestrator', role: 'Coordinates session', icon: RadioTower, color: 'text-sky-300', ring: 'border-sky-400/25 bg-sky-400/8' },
  { id: 'B', name: 'Attacker', role: 'Creates hostile payload', icon: Bot, color: 'text-rose-300', ring: 'border-rose-400/25 bg-rose-400/8' },
  { id: 'C', name: 'Propagator', role: 'Relays agent message', icon: Route, color: 'text-amber-300', ring: 'border-amber-400/25 bg-amber-400/8' },
  { id: 'D', name: 'Defender', role: 'Enforces Guardian policy', icon: Shield, color: 'text-emerald-300', ring: 'border-emerald-400/25 bg-emerald-400/8' },
]

export function AgentFlow() {
  return (
    <div className="mt-6 grid grid-cols-1 gap-3 md:grid-cols-[1fr_auto_1fr_auto_1fr_auto_1fr] md:items-center">
      {agents.map((agent, index) => {
        const Icon = agent.icon
        return (
          <div key={agent.id} className="contents">
            <article className="group rounded-2xl border border-white/8 bg-[#080d17] p-4 transition hover:-translate-y-1 hover:border-white/15">
              <div className={`flex size-11 items-center justify-center rounded-xl border ${agent.ring} ${agent.color}`}>
                <Icon size={21} aria-hidden="true" />
              </div>
              <div className="mt-5 flex items-center gap-2">
                <span className="font-mono text-[10px] font-semibold text-slate-600">AGENT {agent.id}</span>
                <span className="size-1.5 rounded-full bg-emerald-400" />
              </div>
              <h3 className="mt-1 text-sm font-semibold text-white">{agent.name}</h3>
              <p className="mt-1 text-[11px] leading-4 text-slate-500">{agent.role}</p>
            </article>

            {index < agents.length - 1 && (
              <div className="relative mx-auto h-6 w-px bg-white/10 md:h-px md:w-6" aria-hidden="true">
                <span className="absolute bottom-0 left-1/2 size-1.5 -translate-x-1/2 rotate-45 border-r border-b border-slate-600 md:top-1/2 md:right-0 md:bottom-auto md:left-auto md:-translate-y-1/2" />
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

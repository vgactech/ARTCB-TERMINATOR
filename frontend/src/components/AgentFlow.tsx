import { motion } from 'framer-motion'
import { Bot, RadioTower, Route, Shield } from 'lucide-react'

const agents = [
  { id: 'A', name: 'Orchestrator', role: 'Coordinates session', icon: RadioTower, color: 'text-sky-300', ring: 'border-sky-400/25 bg-sky-400/8' },
  { id: 'B', name: 'Attacker', role: 'Creates hostile payload', icon: Bot, color: 'text-rose-300', ring: 'border-rose-400/25 bg-rose-400/8' },
  { id: 'C', name: 'Propagator', role: 'Relays agent message', icon: Route, color: 'text-amber-300', ring: 'border-amber-400/25 bg-amber-400/8' },
  { id: 'D', name: 'Defender', role: 'Enforces Guardian policy', icon: Shield, color: 'text-emerald-300', ring: 'border-emerald-400/25 bg-emerald-400/8' },
]

type AgentFlowProps = {
  activeAgent: number
  running: boolean
}

export function AgentFlow({ activeAgent, running }: AgentFlowProps) {
  return (
    <div className="mt-6 grid min-w-0 grid-cols-1 gap-3 md:grid-cols-[1fr_auto_1fr_auto_1fr_auto_1fr] md:items-center">
      {agents.map((agent, index) => {
        const Icon = agent.icon
        return (
          <div key={agent.id} className="contents">
            <motion.article
              animate={activeAgent === index ? { y: -5, scale: 1.025 } : { y: 0, scale: 1 }}
              className={`group relative min-w-0 rounded-2xl border bg-[#080d17] p-4 transition ${
                activeAgent === index ? 'border-emerald-300/50 shadow-lg shadow-emerald-950/40' : 'border-white/8'
              }`}
            >
              {activeAgent === index && (
                <motion.span
                  layoutId="active-agent"
                  className="absolute inset-x-4 top-0 h-px bg-emerald-300 shadow-[0_0_14px_2px_rgba(110,231,183,0.5)]"
                />
              )}
              <div className={`flex size-11 items-center justify-center rounded-xl border ${agent.ring} ${agent.color}`}>
                <Icon size={21} aria-hidden="true" />
              </div>
              <div className="mt-5 flex items-center gap-2">
                <span className="font-mono text-[10px] font-semibold text-slate-600">AGENT {agent.id}</span>
                <span className={`size-1.5 rounded-full ${activeAgent >= index ? 'bg-emerald-400' : 'bg-slate-700'}`} />
              </div>
              <h3 className="mt-1 text-sm font-semibold text-white">{agent.name}</h3>
              <p className="mt-1 text-[11px] leading-4 text-slate-500">{agent.role}</p>
            </motion.article>

            {index < agents.length - 1 && (
              <div className="relative mx-auto h-6 w-px overflow-hidden bg-white/10 md:h-px md:w-6" aria-hidden="true">
                {running && activeAgent === index && (
                  <motion.span
                    initial={{ y: '-100%', x: 0 }}
                    animate={{ y: '100%', x: 0 }}
                    transition={{ duration: 0.7, repeat: Infinity }}
                    className="absolute inset-x-0 h-1/2 bg-emerald-300 md:inset-y-0 md:h-auto md:w-1/2"
                  />
                )}
                <span className="absolute bottom-0 left-1/2 size-1.5 -translate-x-1/2 rotate-45 border-r border-b border-slate-600 md:top-1/2 md:right-0 md:bottom-auto md:left-auto md:-translate-y-1/2" />
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

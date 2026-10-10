import { motion } from 'framer-motion'
import {
  Activity,
  Bell,
  CircleCheck,
  Play,
  Radar,
  ShieldCheck,
} from 'lucide-react'

const metrics = [
  { label: 'System status', value: 'Protected', detail: 'All controls active', tone: 'emerald' },
  { label: 'Agents online', value: '4 / 4', detail: 'Network synchronized', tone: 'cyan' },
  { label: 'Evidence chain', value: 'Verified', detail: 'Integrity intact', tone: 'violet' },
]

function App() {
  return (
    <main className="min-h-screen bg-[#05080f] text-slate-100">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_70%_0%,rgba(16,185,129,0.09),transparent_35%)]" />

      <header className="relative border-b border-white/8 bg-[#070b14]/90 backdrop-blur-xl">
        <div className="mx-auto flex h-18 max-w-7xl items-center justify-between px-5 lg:px-8">
          <div className="flex items-center gap-3">
            <div className="flex size-10 items-center justify-center rounded-xl border border-emerald-400/25 bg-emerald-400/10 text-emerald-300">
              <ShieldCheck size={23} aria-hidden="true" />
            </div>
            <div>
              <p className="text-sm font-semibold tracking-[0.12em] text-white">ARTCB TERMINATOR</p>
              <p className="text-[11px] text-slate-500">Guardian Security Console</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <span className="hidden items-center gap-2 rounded-full border border-emerald-400/20 bg-emerald-400/7 px-3 py-1.5 text-xs text-emerald-300 sm:flex">
              <span className="size-1.5 animate-pulse rounded-full bg-emerald-300" />
              Engine online
            </span>
            <button className="rounded-xl border border-white/8 p-2.5 text-slate-400 transition hover:border-white/15 hover:text-white" aria-label="Notifications">
              <Bell size={18} />
            </button>
          </div>
        </div>
      </header>

      <div className="relative mx-auto max-w-7xl px-5 py-8 lg:px-8 lg:py-10">
        <section className="flex flex-col justify-between gap-6 md:flex-row md:items-end">
          <div>
            <div className="mb-3 flex items-center gap-2 font-mono text-xs font-semibold tracking-[0.2em] text-emerald-300 uppercase">
              <Radar size={15} /> Live defense environment
            </div>
            <h1 className="text-3xl font-semibold tracking-tight text-white md:text-5xl">Security operations overview</h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400 md:text-base">
              Observe the complete agent attack path, policy decision, evidence chain, and deterministic replay from one console.
            </p>
          </div>
          <motion.button
            whileHover={{ y: -2 }}
            whileTap={{ scale: 0.98 }}
            className="inline-flex min-h-12 items-center justify-center gap-2 rounded-xl bg-emerald-400 px-5 font-semibold text-slate-950 shadow-lg shadow-emerald-950/40 transition hover:bg-emerald-300"
          >
            <Play size={18} fill="currentColor" /> Run attack simulation
          </motion.button>
        </section>

        <section className="mt-8 grid gap-4 md:grid-cols-3">
          {metrics.map((metric, index) => (
            <motion.article
              key={metric.label}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.08 }}
              className="rounded-2xl border border-white/8 bg-slate-950/55 p-5 shadow-xl shadow-black/10"
            >
              <div className="flex items-start justify-between">
                <p className="text-sm text-slate-500">{metric.label}</p>
                <CircleCheck size={17} className={`text-${metric.tone}-300`} />
              </div>
              <p className="mt-4 text-2xl font-semibold text-white">{metric.value}</p>
              <p className="mt-1 text-xs text-slate-500">{metric.detail}</p>
            </motion.article>
          ))}
        </section>

        <section className="mt-6 grid gap-6 lg:grid-cols-[1.65fr_1fr]">
          <article className="min-h-96 rounded-2xl border border-white/8 bg-slate-950/55 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-semibold text-white">Agent network</p>
                <p className="mt-1 text-xs text-slate-500">Live execution path</p>
              </div>
              <Activity size={18} className="text-emerald-300" />
            </div>
            <div className="grid min-h-72 place-items-center rounded-xl border border-dashed border-white/8 bg-white/[0.015] text-sm text-slate-600">
              Agent visualization will appear here
            </div>
          </article>

          <article className="min-h-96 rounded-2xl border border-white/8 bg-slate-950/55 p-6">
            <p className="text-sm font-semibold text-white">Latest operation</p>
            <p className="mt-1 text-xs text-slate-500">Awaiting simulation</p>
            <div className="mt-6 grid min-h-72 place-items-center rounded-xl border border-dashed border-white/8 bg-white/[0.015] px-8 text-center">
              <div>
                <ShieldCheck className="mx-auto text-slate-700" size={32} />
                <p className="mt-3 text-sm text-slate-500">Run the attack simulation to generate security evidence.</p>
              </div>
            </div>
          </article>
        </section>
      </div>
    </main>
  )
}

export default App

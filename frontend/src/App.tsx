import { motion } from 'framer-motion'
import { useEffect, useState } from 'react'
import {
  Activity,
  Bell,
  CircleCheck,
  Play,
  Radar,
  ShieldCheck,
} from 'lucide-react'
import { AgentFlow } from './components/AgentFlow'
import { EventTimeline } from './components/EventTimeline'
import { ReplayResults } from './components/ReplayResults'
import { SecurityResults } from './components/SecurityResults'
import { checkGuardianHealth, runGuardianSimulation } from './api/guardian'
import type { SimulationReport } from './api/guardian'

const metrics = [
  { label: 'System status', value: 'Protected', detail: 'All controls active', iconClass: 'text-emerald-300' },
  { label: 'Agents online', value: '4 / 4', detail: 'Network synchronized', iconClass: 'text-cyan-300' },
  { label: 'Evidence chain', value: 'Verified', detail: 'Integrity intact', iconClass: 'text-violet-300' },
]

function App() {
  const [activeAgent, setActiveAgent] = useState(-1)
  const [running, setRunning] = useState(false)
  const [report, setReport] = useState<SimulationReport | null>(null)
  const [apiError, setApiError] = useState('')
  const [engineState, setEngineState] = useState<'checking' | 'online' | 'offline'>('checking')
  const blocked = activeAgent === 4 && report?.blocking?.decision === 'BLOCK'

  useEffect(() => {
    checkGuardianHealth()
      .then(() => setEngineState('online'))
      .catch(() => setEngineState('offline'))
  }, [])

  useEffect(() => {
    if (!running) return
    const timer = window.setInterval(() => {
      setActiveAgent((current) => {
        if (current >= 3) {
          window.clearInterval(timer)
          setRunning(false)
          return 4
        }
        return current + 1
      })
    }, 850)
    return () => window.clearInterval(timer)
  }, [running])

  const runSimulation = async () => {
    setReport(null)
    setApiError('')
    setActiveAgent(0)
    setRunning(true)
    try {
      const nextReport = await runGuardianSimulation()
      setReport(nextReport)
      setEngineState('online')
    } catch (error) {
      setRunning(false)
      setActiveAgent(-1)
      setEngineState('offline')
      setApiError(error instanceof Error ? error.message : 'Guardian simulation failed.')
    }
  }

  return (
    <main className="min-h-screen overflow-x-hidden bg-[#05080f] text-slate-100">
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
              <span className={`size-1.5 rounded-full ${engineState === 'online' ? 'animate-pulse bg-emerald-300' : engineState === 'offline' ? 'bg-rose-400' : 'animate-pulse bg-amber-300'}`} />
              {engineState === 'online' ? 'Engine online' : engineState === 'offline' ? 'Engine offline' : 'Checking engine'}
            </span>
            <button type="button" className="rounded-xl border border-white/8 p-2.5 text-slate-400 transition hover:border-white/15 hover:text-white focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-300" aria-label="Notifications">
              <Bell size={18} />
            </button>
          </div>
        </div>
      </header>

      <div className="relative mx-auto max-w-7xl px-5 py-8 lg:px-8 lg:py-10">
        <section className="flex min-w-0 flex-col justify-between gap-6 md:flex-row md:items-end">
          <div className="min-w-0">
            <div className="mb-3 flex items-center gap-2 font-mono text-xs font-semibold tracking-[0.2em] text-emerald-300 uppercase">
              <Radar size={15} /> Live defense environment
            </div>
            <h1 className="text-3xl font-semibold tracking-tight text-balance text-white md:text-5xl">Security operations overview</h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400 md:text-base">
              Observe the complete agent attack path, policy decision, evidence chain, and deterministic replay from one console.
            </p>
          </div>
          <motion.button
            type="button"
            whileHover={{ y: -2 }}
            whileTap={{ scale: 0.98 }}
            onClick={runSimulation}
            disabled={running}
            aria-busy={running}
            aria-describedby="simulation-status"
            className="inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-xl bg-emerald-400 px-5 font-semibold text-slate-950 shadow-lg shadow-emerald-950/40 transition hover:bg-emerald-300 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-emerald-300 disabled:cursor-wait disabled:opacity-60 md:w-auto"
          >
            <Play size={18} fill="currentColor" aria-hidden="true" /> {running ? 'Simulation running…' : 'Run attack simulation'}
          </motion.button>
          <span id="simulation-status" className="sr-only" aria-live="polite">
            {apiError || (blocked ? 'Simulation complete. Hostile action blocked.' : running ? `Simulation running. Processing agent ${activeAgent + 1} of 4.` : 'Simulation ready.')}
          </span>
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
                <CircleCheck size={17} className={metric.iconClass} aria-hidden="true" />
              </div>
              <p className="mt-4 text-2xl font-semibold text-white">{metric.value}</p>
              <p className="mt-1 text-xs text-slate-500">{metric.detail}</p>
            </motion.article>
          ))}
        </section>

        <section className="mt-6 grid gap-6 lg:grid-cols-[1.65fr_1fr]">
          <article className="min-h-96 rounded-2xl border border-white/8 bg-slate-950/55 p-4 sm:p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-semibold text-white">Agent network</p>
                <p className="mt-1 text-xs text-slate-500">Live execution path</p>
              </div>
              <Activity size={18} className="text-emerald-300" aria-hidden="true" />
            </div>
            <AgentFlow activeAgent={activeAgent} running={running} />
            <div className="mt-5 flex items-center justify-between rounded-xl border border-white/6 bg-white/[0.02] px-4 py-3 text-xs">
              <span className="text-slate-500">Protected execution boundary</span>
              <span className="font-mono text-emerald-300">4 NODES · READY</span>
            </div>
          </article>

          <article className="min-h-96 rounded-2xl border border-white/8 bg-slate-950/55 p-4 sm:p-6">
            <p className="text-sm font-semibold text-white">Latest operation</p>
            <p className="mt-1 text-xs text-slate-500">{blocked ? 'Threat contained' : running ? 'Analyzing agent traffic' : 'Awaiting simulation'}</p>
            <div className="mt-6 grid min-h-72 place-items-center rounded-xl border border-dashed border-white/8 bg-white/[0.015] px-8 text-center">
              {apiError ? (
                <div role="alert">
                  <div className="mx-auto flex size-16 items-center justify-center rounded-2xl border border-rose-400/25 bg-rose-400/10 text-rose-300">
                    <ShieldCheck size={34} aria-hidden="true" />
                  </div>
                  <p className="mt-4 font-mono text-xs font-bold tracking-[0.2em] text-rose-300">BACKEND OFFLINE</p>
                  <p className="mt-2 text-sm leading-6 text-slate-400">{apiError}</p>
                </div>
              ) : blocked ? (
                <motion.div initial={{ scale: 0.85, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}>
                  <div className="mx-auto flex size-16 items-center justify-center rounded-2xl border border-rose-400/25 bg-rose-400/10 text-rose-300">
                    <ShieldCheck size={34} />
                  </div>
                  <p className="mt-4 font-mono text-xs font-bold tracking-[0.24em] text-rose-300">ACTION BLOCKED</p>
                  <p className="mt-2 text-sm text-slate-400">Sensitive tool execution prevented by Guardian.</p>
                </motion.div>
              ) : (
                <div>
                  <ShieldCheck className={`mx-auto ${running ? 'animate-pulse text-emerald-400' : 'text-slate-700'}`} size={32} />
                  <p className="mt-3 text-sm text-slate-500">{running ? 'Tracing the hostile payload across agents…' : 'Run the attack simulation to generate security evidence.'}</p>
                </div>
              )}
            </div>
          </article>
        </section>

        {blocked && report && (
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}>
            <SecurityResults
              evidenceId={report.blocking?.evidence_id ?? ''}
              sessionId={report.session_id}
              runId={report.run_id}
            />
            <EventTimeline />
            <ReplayResults />
          </motion.div>
        )}

        <footer className="mt-10 border-t border-white/6 py-6 text-center text-xs text-slate-600">
          ARTCB TERMINATOR · Guardian Security Console
        </footer>
      </div>
    </main>
  )
}

export default App

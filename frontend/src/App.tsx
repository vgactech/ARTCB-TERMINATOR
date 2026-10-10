import { motion } from 'framer-motion'
import { useEffect, useState } from 'react'
import { Activity, Bell, CircleCheck, Play, Radar, ShieldCheck } from 'lucide-react'
import { AgentFlow } from './components/AgentFlow'
import { EventTimeline } from './components/EventTimeline'
import { OrchestrationProof } from './components/OrchestrationProof'
import { ReplayResults } from './components/ReplayResults'
import { SecurityResults } from './components/SecurityResults'
import { checkGuardianHealth, listGuardianScenarios, runGuardianScenario } from './api/guardian'
import type { PolicyScenario, PolicyScenarioResult } from './api/guardian'

function App() {
  const [activeAgent, setActiveAgent] = useState(-1)
  const [running, setRunning] = useState(false)
  const [scenarios, setScenarios] = useState<PolicyScenario[]>([])
  const [selectedScenario, setSelectedScenario] = useState('sensitive-exfiltration')
  const [result, setResult] = useState<PolicyScenarioResult | null>(null)
  const [apiError, setApiError] = useState('')
  const [engineState, setEngineState] = useState<'checking' | 'online' | 'offline'>('checking')
  const completed = activeAgent === 4 && result !== null

  useEffect(() => {
    Promise.all([checkGuardianHealth(), listGuardianScenarios()])
      .then(([, available]) => {
        setScenarios(available)
        setEngineState('online')
      })
      .catch(() => setEngineState('offline'))
  }, [])

  const runSimulation = async () => {
    setResult(null)
    setApiError('')
    setActiveAgent(-1)
    setRunning(true)
    try {
      const nextResult = await runGuardianScenario(selectedScenario)
      setResult(nextResult)
      setEngineState('online')
      for (const stage of nextResult.agents) {
        setActiveAgent(stage.index)
        await new Promise((resolve) => window.setTimeout(resolve, 450))
      }
      setActiveAgent(4)
      setRunning(false)
    } catch (error) {
      setRunning(false)
      setActiveAgent(-1)
      setEngineState('offline')
      setApiError(error instanceof Error ? error.message : 'Guardian simulation failed.')
    }
  }

  const metrics = [
    { label: 'System status', value: engineState === 'online' ? 'Protected' : engineState === 'offline' ? 'Offline' : 'Checking', detail: 'Live backend connection', iconClass: engineState === 'offline' ? 'text-rose-300' : 'text-emerald-300' },
    { label: 'Agents participating', value: result ? `${result.distinct_agent_count} / 4` : 'Ready', detail: result ? 'Distinct backend instances verified' : 'Awaiting execution', iconClass: 'text-cyan-300' },
    { label: 'Evidence chain', value: result?.chain_verification.verdict ?? 'Ready', detail: result ? `${result.events.length} real events recorded` : 'Awaiting execution', iconClass: 'text-violet-300' },
  ]

  return (
    <main className="min-h-screen overflow-x-hidden bg-[#05080f] text-slate-100">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_70%_0%,rgba(16,185,129,0.09),transparent_35%)]" />
      <header className="relative border-b border-white/8 bg-[#070b14]/90 backdrop-blur-xl">
        <div className="mx-auto flex h-18 max-w-7xl items-center justify-between px-5 lg:px-8">
          <div className="flex items-center gap-3">
            <div className="flex size-10 items-center justify-center rounded-xl border border-emerald-400/25 bg-emerald-400/10 text-emerald-300"><ShieldCheck size={23} aria-hidden="true" /></div>
            <div><p className="text-sm font-semibold tracking-[0.12em] text-white">ARTCB TERMINATOR</p><p className="text-[11px] text-slate-500">Guardian Security Console</p></div>
          </div>
          <div className="flex items-center gap-3">
            <span className="hidden items-center gap-2 rounded-full border border-white/10 bg-white/[0.03] px-3 py-1.5 text-xs text-slate-300 sm:flex">
              <span className={`size-1.5 rounded-full ${engineState === 'online' ? 'animate-pulse bg-emerald-300' : engineState === 'offline' ? 'bg-rose-400' : 'animate-pulse bg-amber-300'}`} />
              {engineState === 'online' ? 'Engine online' : engineState === 'offline' ? 'Engine offline' : 'Checking engine'}
            </span>
            <button type="button" className="rounded-xl border border-white/8 p-2.5 text-slate-400 transition hover:text-white focus-visible:outline-2 focus-visible:outline-emerald-300" aria-label="Notifications"><Bell size={18} /></button>
          </div>
        </div>
      </header>

      <div className="relative mx-auto max-w-7xl px-5 py-8 lg:px-8 lg:py-10">
        <section className="flex min-w-0 flex-col justify-between gap-6 md:flex-row md:items-end">
          <div className="min-w-0">
            <div className="mb-3 flex items-center gap-2 font-mono text-xs font-semibold tracking-[0.2em] text-emerald-300 uppercase"><Radar size={15} /> Live defense environment</div>
            <h1 className="text-3xl font-semibold tracking-tight text-balance text-white md:text-5xl">Security operations overview</h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400 md:text-base">Run security requests through four distinct backend agents and inspect Guardian's policy evidence.</p>
          </div>
          <motion.button type="button" whileHover={{ y: -2 }} whileTap={{ scale: 0.98 }} onClick={runSimulation} disabled={running || engineState !== 'online'} aria-busy={running} aria-describedby="simulation-status" className="inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-xl bg-emerald-400 px-5 font-semibold text-slate-950 transition hover:bg-emerald-300 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-emerald-300 disabled:cursor-wait disabled:opacity-60 md:w-auto">
            <Play size={18} fill="currentColor" aria-hidden="true" /> {running ? 'Guardian evaluating…' : 'Run selected scenario'}
          </motion.button>
          <span id="simulation-status" className="sr-only" aria-live="polite">{apiError || (completed ? `Guardian returned ${result.decision}.` : running ? `Processing agent ${activeAgent + 1} of 4.` : 'Simulation ready.')}</span>
        </section>

        <section className="mt-8" aria-labelledby="scenario-heading">
          <div className="flex items-end justify-between gap-4">
            <div><h2 id="scenario-heading" className="text-sm font-semibold text-white">Choose a live policy scenario</h2><p className="mt-1 text-xs text-slate-500">Each option is evaluated by the Guardian backend.</p></div>
            <span className="font-mono text-[10px] text-slate-600">{scenarios.length} AVAILABLE</span>
          </div>
          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {scenarios.map((scenario) => (
              <button key={scenario.id} type="button" disabled={running} onClick={() => setSelectedScenario(scenario.id)} className={`rounded-xl border p-4 text-left transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-300 ${selectedScenario === scenario.id ? 'border-emerald-400/40 bg-emerald-400/[0.07]' : 'border-white/8 bg-slate-950/55 hover:border-white/15'}`}>
                <span className="font-mono text-[10px] font-bold text-emerald-300">{scenario.risk} RISK</span><span className="mt-2 block text-sm font-semibold text-white">{scenario.name}</span><span className="mt-1 block text-xs leading-5 text-slate-500">{scenario.description}</span>
              </button>
            ))}
          </div>
        </section>

        <section className="mt-8 grid gap-4 md:grid-cols-3">
          {metrics.map((metric, index) => <motion.article key={metric.label} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.08 }} className="rounded-2xl border border-white/8 bg-slate-950/55 p-5"><div className="flex items-start justify-between"><p className="text-sm text-slate-500">{metric.label}</p><CircleCheck size={17} className={metric.iconClass} aria-hidden="true" /></div><p className="mt-4 text-2xl font-semibold text-white">{metric.value}</p><p className="mt-1 text-xs text-slate-500">{metric.detail}</p></motion.article>)}
        </section>

        <section className="mt-6 grid gap-6 lg:grid-cols-[1.65fr_1fr]">
          <article className="min-h-96 rounded-2xl border border-white/8 bg-slate-950/55 p-4 sm:p-6">
            <div className="flex items-center justify-between"><div><p className="text-sm font-semibold text-white">Four-agent execution trace</p><p className="mt-1 text-xs text-slate-500">Backend-reported orchestration path</p></div><Activity size={18} className="text-emerald-300" aria-hidden="true" /></div>
            <AgentFlow activeAgent={activeAgent} running={running} stages={result?.agents} />
            <div className="mt-5 flex items-center justify-between rounded-xl border border-white/6 bg-white/[0.02] px-4 py-3 text-xs"><span className="text-slate-500">Protected execution boundary</span><span className="font-mono text-emerald-300">4 NODES · READY</span></div>
          </article>
          <article className="min-h-96 rounded-2xl border border-white/8 bg-slate-950/55 p-4 sm:p-6">
            <p className="text-sm font-semibold text-white">Latest operation</p><p className="mt-1 text-xs text-slate-500">{completed ? `${result.decision}: ${result.reason}` : running ? 'Analyzing agent traffic' : 'Awaiting scenario'}</p>
            <div className="mt-6 grid min-h-72 place-items-center rounded-xl border border-dashed border-white/8 bg-white/[0.015] px-8 text-center">
              {apiError ? <div role="alert"><p className="font-mono text-xs font-bold text-rose-300">BACKEND OFFLINE</p><p className="mt-2 text-sm leading-6 text-slate-400">{apiError}</p></div> : completed ? (
                <motion.div initial={{ scale: 0.85, opacity: 0 }} animate={{ scale: 1, opacity: 1 }}>
                  <div className={`mx-auto flex size-16 items-center justify-center rounded-2xl border ${result.decision === 'ALLOW' ? 'border-emerald-400/25 bg-emerald-400/10 text-emerald-300' : result.decision === 'ESCALATE' ? 'border-amber-400/25 bg-amber-400/10 text-amber-300' : 'border-rose-400/25 bg-rose-400/10 text-rose-300'}`}><ShieldCheck size={34} aria-hidden="true" /></div>
                  <p className="mt-4 font-mono text-xs font-bold tracking-[0.24em] text-white">{result.decision}</p><p className="mt-2 text-sm text-slate-400">{result.tool_name}: {result.execution_status.replace('_', ' ').toLowerCase()}.</p>
                </motion.div>
              ) : <div><ShieldCheck className={`mx-auto ${running ? 'animate-pulse text-emerald-400' : 'text-slate-700'}`} size={32} aria-hidden="true" /><p className="mt-3 text-sm text-slate-500">{running ? 'Guardian is evaluating the request…' : 'Choose a scenario and run it against the backend.'}</p></div>}
            </div>
          </article>
        </section>

        {completed && result && <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}><OrchestrationProof result={result} /><SecurityResults result={result} /><EventTimeline events={result.events} /><ReplayResults result={result} /></motion.div>}
        <footer className="mt-10 border-t border-white/6 py-6 text-center text-xs text-slate-600">ARTCB TERMINATOR · Guardian Security Console</footer>
      </div>
    </main>
  )
}

export default App

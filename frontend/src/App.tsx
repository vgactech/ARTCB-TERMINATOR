import { motion } from 'framer-motion'
import { lazy, Suspense, useEffect, useState } from 'react'
import { Activity, CircleCheck, Play, ShieldCheck } from 'lucide-react'
import { AgentFlow } from './components/AgentFlow'
import { checkGuardianHealth, listGuardianScenarios, runGuardianScenario } from './api/guardian'
import type { PolicyScenario, PolicyScenarioResult } from './api/guardian'

const ExecutionGraphOverlay = lazy(() =>
  import('./components/ExecutionGraphOverlay').then((module) => ({ default: module.ExecutionGraphOverlay })),
)

const scenarioDescriptions: Record<string, string> = {
  'safe-read': 'Normal request',
  'prompt-injection': 'Malicious instruction',
  'sensitive-exfiltration': 'Protected tool access',
  'human-approval': 'Manual review required',
}

function App() {
  const [activeAgent, setActiveAgent] = useState(-1)
  const [running, setRunning] = useState(false)
  const [scenarios, setScenarios] = useState<PolicyScenario[]>([])
  const [selectedScenario, setSelectedScenario] = useState('sensitive-exfiltration')
  const [result, setResult] = useState<PolicyScenarioResult | null>(null)
  const [apiError, setApiError] = useState('')
  const [graphOpen, setGraphOpen] = useState(false)
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
    setGraphOpen(true)
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
    { label: 'Backend', value: engineState === 'online' ? 'Online' : engineState === 'offline' ? 'Offline' : 'Checking', iconClass: engineState === 'offline' ? 'text-rose-300' : 'text-emerald-300' },
    { label: 'Agents verified', value: result ? `${result.distinct_agent_count} of 4` : 'Waiting', iconClass: 'text-cyan-300' },
    { label: 'Audit trail', value: result ? (result.chain_verification.verdict === 'PASS' ? 'Valid' : 'Invalid') : 'Waiting', iconClass: 'text-violet-300' },
  ]

  return (
    <main className="min-h-screen overflow-x-hidden bg-[linear-gradient(145deg,#0b1b30_0%,#0a1728_45%,#092526_100%)] text-slate-100">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_72%_5%,rgba(34,211,238,0.1),transparent_34%),radial-gradient(circle_at_12%_42%,rgba(16,185,129,0.08),transparent_30%)]" />
      <header className="relative border-b border-white/8 bg-[#0a1627]/82 backdrop-blur-xl">
        <div className="mx-auto flex h-18 max-w-7xl items-center justify-between px-5 lg:px-8">
          <div className="flex items-center gap-3">
            <div className="flex size-10 items-center justify-center rounded-xl border border-emerald-400/25 bg-emerald-400/10 text-emerald-300"><ShieldCheck size={23} aria-hidden="true" /></div>
            <div><p className="text-sm font-semibold tracking-[0.12em] text-white">ARTCB TERMINATOR</p><p className="text-[11px] text-slate-500">Guardian Security Console</p></div>
          </div>
        </div>
      </header>

      <div className="relative mx-auto max-w-7xl px-5 py-8 lg:px-8 lg:py-10">
        <section className="min-w-0">
          <div className="min-w-0">
            <h1 className="text-3xl font-semibold tracking-tight text-balance text-white md:text-5xl">Security operations overview</h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-slate-400 md:text-base">Test requests through four Guardian agents.</p>
          </div>
          <span id="simulation-status" className="sr-only" aria-live="polite">{apiError || (completed ? `Guardian returned ${result.decision}.` : running ? `Processing agent ${activeAgent + 1} of 4.` : 'Simulation ready.')}</span>
        </section>

        <section className="mt-8" aria-labelledby="scenario-heading">
          <div className="flex items-end justify-between gap-4">
            <h2 id="scenario-heading" className="text-lg font-semibold tracking-tight text-white sm:text-xl">Choose a live policy scenario</h2>
            <span className="font-mono text-[10px] text-slate-600">{scenarios.length} AVAILABLE</span>
          </div>
          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {scenarios.map((scenario) => (
              <button key={scenario.id} type="button" disabled={running} onClick={() => setSelectedScenario(scenario.id)} className={`rounded-xl border p-4 text-left transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-300 ${selectedScenario === scenario.id ? 'border-emerald-400/40 bg-emerald-400/[0.07]' : 'border-white/8 bg-slate-950/55 hover:border-white/15'}`}>
                <span className="font-mono text-[10px] font-bold text-emerald-300">{scenario.risk} RISK</span><span className="mt-2 block text-sm font-semibold text-white">{scenario.name}</span><span className="mt-1 block text-xs leading-5 text-slate-500">{scenarioDescriptions[scenario.id]}</span>
              </button>
            ))}
          </div>
          <motion.button type="button" whileHover={{ y: -2 }} whileTap={{ scale: 0.98 }} onClick={runSimulation} disabled={running || engineState !== 'online'} aria-busy={running} aria-describedby="simulation-status" className="mt-5 inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-xl bg-emerald-400 px-5 font-semibold text-slate-950 transition hover:bg-emerald-300 focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-emerald-300 disabled:cursor-wait disabled:opacity-60 sm:w-auto">
            <Play size={18} fill="currentColor" aria-hidden="true" /> {running ? 'Guardian evaluating…' : 'Run selected scenario'}
          </motion.button>
          {apiError && <p role="alert" className="mt-3 text-sm text-rose-300">{apiError}</p>}
        </section>

        <section className="mt-8">
          <article className="rounded-2xl border border-white/8 bg-slate-950/55 p-4 sm:p-6">
            <div className="flex items-center justify-between gap-3"><div><p className="text-sm font-semibold text-white">Four-agent execution trace</p><p className="mt-1 text-xs text-slate-500">Backend-reported orchestration path</p></div>{result && <button type="button" onClick={() => setGraphOpen(true)} className="flex items-center gap-2 rounded-lg border border-cyan-400/20 bg-cyan-400/[0.05] px-3 py-2 text-xs text-cyan-300 transition hover:bg-cyan-400/10"><Activity size={15} aria-hidden="true" /> View execution graph</button>}</div>
            <AgentFlow activeAgent={activeAgent} running={running} stages={result?.agents} />
          </article>
        </section>

        <section className="mt-6 grid gap-4 md:grid-cols-3">
          {metrics.map((metric, index) => <motion.article key={metric.label} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: index * 0.08 }} className="rounded-2xl border border-white/8 bg-slate-950/55 p-5"><div className="flex items-start justify-between"><p className="text-sm text-slate-500">{metric.label}</p><CircleCheck size={17} className={metric.iconClass} aria-hidden="true" /></div><p className="mt-4 text-2xl font-semibold text-white">{metric.value}</p></motion.article>)}
        </section>

        <footer className="mt-10 border-t border-white/6 py-6 text-center text-xs text-slate-600">ARTCB TERMINATOR · Guardian Security Console</footer>
      </div>
      {graphOpen && <Suspense fallback={<div className="fixed inset-0 z-50 grid place-items-center bg-black/75 text-sm text-cyan-300">Loading execution graph…</div>}><ExecutionGraphOverlay open result={result} activeAgent={activeAgent} onClose={() => setGraphOpen(false)} /></Suspense>}
    </main>
  )
}

export default App

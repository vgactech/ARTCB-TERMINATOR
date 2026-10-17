import { lazy, Suspense, useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Activity, ShieldCheck, Play, CircleCheck } from 'lucide-react'
import { KycPanel } from './components/KycPanel'
import { PitchPage } from './components/PitchPage'
import { AgentFlow } from './components/AgentFlow'
import { ForensicPanel } from './components/ForensicPanel'
import { checkGuardianHealth, listGuardianScenarios, runGuardianScenario } from './api/guardian'
import type { PolicyScenario, PolicyScenarioResult } from './api/guardian'
import { phaseFromResult, phaseFromAgentIndex } from './forensic/phases'
import type { ForensicPhase } from './forensic/phases'

const ExecutionGraphOverlay = lazy(() =>
  import('./components/ExecutionGraphOverlay').then((m) => ({ default: m.ExecutionGraphOverlay })),
)

const API_BASE = import.meta.env.VITE_API_URL?.replace(/\/$/, '') ?? ''

const scenarioDescriptions: Record<string, string> = {
  'safe-read':              'Requête normale',
  'prompt-injection':       'Instruction malveillante',
  'sensitive-exfiltration': 'Outil protégé ciblé',
  'human-approval':         'Revue manuelle requise',
}

function App() {
  // ── Engine state ────────────────────────────────────────────────────────
  const [engineState, setEngineState] = useState<'checking' | 'online' | 'offline'>('checking')
  const [scenarios,   setScenarios]   = useState<PolicyScenario[]>([])

  // ── Scenario runner ──────────────────────────────────────────────────────
  const [selectedScenario, setSelectedScenario] = useState('sensitive-exfiltration')
  const [running,          setRunning]           = useState(false)
  const [activeAgent,      setActiveAgent]       = useState(-1)
  const [result,           setResult]            = useState<PolicyScenarioResult | null>(null)
  const [apiError,         setApiError]          = useState('')
  const [graphOpen,        setGraphOpen]         = useState(false)
  const [forensicPhase,    setForensicPhase]     = useState<ForensicPhase>('idle')

  // ── KYC ───────────────────────────────────────────────────────────────────
  const [showHudGraph,     setShowHudGraph]      = useState(true)

  // ── Active tab ────────────────────────────────────────────────────────────
  const [tab, setTab] = useState<'pitch' | 'kyc' | 'scenarios'>('pitch')

  useEffect(() => {
    Promise.all([checkGuardianHealth(), listGuardianScenarios()])
      .then(([, available]) => {
        setScenarios(available)
        setEngineState('online')
      })
      .catch(() => setEngineState('offline'))
  }, [])

  // ── Scenario runner ──────────────────────────────────────────────────────
  const runSimulation = async () => {
    setResult(null)
    setApiError('')
    setActiveAgent(-1)
    setForensicPhase('scenario_start')
    setRunning(true)
    setGraphOpen(true)
    try {
      const nextResult = await runGuardianScenario(selectedScenario)
      setResult(nextResult)
      setEngineState('online')
      for (const stage of nextResult.agents) {
        setActiveAgent(stage.index)
        setForensicPhase(phaseFromAgentIndex(stage.index, nextResult.decision))
        await new Promise((r) => window.setTimeout(r, 450))
      }
      setActiveAgent(4)
      setForensicPhase(phaseFromResult(nextResult))
      setRunning(false)
    } catch (err) {
      setRunning(false)
      setActiveAgent(-1)
      setForensicPhase('verification_incomplete')
      setEngineState('offline')
      setApiError(err instanceof Error ? err.message : 'Simulation failed.')
    }
  }

  // ── KYC SSE feed is handled inside KycPanel (timeline + embedded graph) ──
  const metrics = [
    { label: 'Backend',          value: engineState === 'online' ? 'Online' : engineState === 'offline' ? 'Offline' : 'Checking…', iconClass: engineState === 'offline' ? 'text-rose-300' : 'text-emerald-300' },
    { label: 'Agents vérifiés',  value: result ? `${result.distinct_agent_count}/4` : 'En attente',   iconClass: 'text-cyan-300' },
    { label: 'Chaîne audit',     value: result ? (result.chain_verification.verdict === 'PASS' ? 'Valide' : 'Invalide') : 'En attente', iconClass: 'text-violet-300' },
  ]

  return (
    <main className="min-h-screen overflow-x-hidden bg-[linear-gradient(145deg,#0b1b30_0%,#0a1728_45%,#092526_100%)] text-slate-100">
      {/* Background gradients */}
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_72%_5%,rgba(34,211,238,0.08),transparent_34%),radial-gradient(circle_at_12%_42%,rgba(16,185,129,0.06),transparent_30%)]" />

      {/* ── Header ────────────────────────────────────────────────────────── */}
      <header className="relative border-b border-white/8 bg-[#0a1627]/85 backdrop-blur-xl sticky top-0 z-30">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-3 lg:px-8 gap-2">
          <div className="flex items-center gap-2 min-w-0 shrink">
            <div className="flex size-9 shrink-0 items-center justify-center rounded-xl border border-emerald-400/25 bg-emerald-400/10 text-emerald-300">
              <ShieldCheck size={20} />
            </div>
            <div className="min-w-0">
              <p className="text-sm font-bold tracking-[0.12em] text-white truncate">ARTCB TERMINATOR FORENSIC</p>
              <p className="text-[11px] text-slate-400 truncate">Guardian Security Console · KYC · Blockchain</p>
            </div>
          </div>
          <div className="flex items-center gap-2 shrink-0">
            {/* HUD toggle */}
            <button
              onClick={() => setShowHudGraph(v => !v)}
              className={`flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs transition ${showHudGraph ? 'border-cyan-400/30 bg-cyan-400/10 text-cyan-300' : 'border-white/10 text-slate-400 hover:text-slate-200'}`}
            >
              <Activity size={13} /> HUD Graph
            </button>
            {/* Engine badge */}
            <span className={`flex items-center gap-1 rounded-full border px-2.5 py-1 text-[11px] font-semibold whitespace-nowrap ${engineState === 'online' ? 'border-emerald-400/30 bg-emerald-400/10 text-emerald-300' : 'border-rose-400/30 bg-rose-400/10 text-rose-300'}`}>
              <span className={`size-1.5 rounded-full shrink-0 ${engineState === 'online' ? 'bg-emerald-400 animate-pulse' : 'bg-rose-400'}`} />
              <span className="hidden sm:inline">{engineState === 'online' ? 'Guardian Online' : engineState === 'offline' ? 'Offline' : 'Connexion…'}</span>
              <span className="sm:hidden">{engineState === 'online' ? 'ON' : engineState === 'offline' ? 'OFF' : '…'}</span>
            </span>
          </div>
        </div>
      </header>

      <div className={`relative mx-auto ${tab === 'kyc' ? 'max-w-none' : 'max-w-7xl'} px-5 py-8 lg:px-8 pb-32`}>

        {/* ── Tabs ──────────────────────────────────────────────────────────── */}
        <div className="flex items-center gap-1 mb-6 bg-slate-950/50 rounded-xl p-1 border border-white/8 w-fit">
          {([
              { id: 'pitch',     label: '🏦 Pitch Jury',          hidden: false },
              { id: 'kyc',       label: '🔍 KYC Forensic',        hidden: false },
              { id: 'scenarios', label: '⚡ Scénarios Guardian',  hidden: false },
            ] as const).filter(t => !t.hidden).map(t => (
              <button
                key={t.id}
                onClick={() => setTab(t.id)}
                className={`px-5 py-2 rounded-lg text-sm font-semibold transition ${tab === t.id ? 'bg-emerald-400/15 border border-emerald-400/30 text-emerald-300' : 'text-slate-400 hover:text-slate-200'}`}
              >
                {t.label}
              </button>
            ))}
        </div>

        {/* ── Pitch Tab ─────────────────────────────────────────────────────── */}
        {tab === 'pitch' && <PitchPage />}

        {/* ── KYC Tab ───────────────────────────────────────────────────────── */}
        {tab === 'kyc' && (
          <div className="space-y-6">
            <div>
              <h1 className="text-2xl font-bold text-white md:text-3xl">Scénario KYC — Know Your Customer</h1>
              <p className="mt-2 text-sm text-slate-400">Traitement d'identité en temps réel · Attaque LLM simulée · Guardian bloque · Rapport PDF signé</p>
            </div>
            <KycPanel apiBase={API_BASE} showGraph={showHudGraph} />
          </div>
        )}

        {/* ── Scenarios Tab ─────────────────────────────────────────────────── */}
        {tab === 'scenarios' && (
          <div className="space-y-6">
            <div>
              <h1 className="text-2xl font-bold text-white md:text-3xl">Scénarios de politique Guardian</h1>
              <p className="mt-2 text-sm text-slate-400">Testez les 4 agents via des requêtes réelles contre Guardian.</p>
            </div>

            {/* Scenario selector */}
            <section aria-labelledby="scenario-heading">
              <div className="flex items-end justify-between gap-4 mb-4">
                <h2 id="scenario-heading" className="text-lg font-semibold text-white">Choisir un scénario</h2>
                <span className="font-mono text-[10px] text-slate-400">{scenarios.length} DISPONIBLES</span>
              </div>
              <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
                {scenarios.map((scenario) => (
                  <button
                    key={scenario.id}
                    type="button"
                    disabled={running}
                    onClick={() => setSelectedScenario(scenario.id)}
                    className={`rounded-xl border p-4 text-left transition focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-300 ${selectedScenario === scenario.id ? 'border-emerald-400/40 bg-emerald-400/[0.07]' : 'border-white/8 bg-slate-950/55 hover:border-white/15'}`}
                  >
                    <span className="font-mono text-[10px] font-bold text-emerald-300">{scenario.risk} RISK</span>
                    <span className="mt-2 block text-sm font-semibold text-white">{scenario.name}</span>
                    <span className="mt-1 block text-xs leading-5 text-slate-400">{scenarioDescriptions[scenario.id] ?? scenario.description}</span>
                  </button>
                ))}
              </div>

              <motion.button
                type="button"
                whileHover={{ y: -2 }}
                whileTap={{ scale: 0.98 }}
                onClick={runSimulation}
                disabled={running || engineState !== 'online'}
                className="mt-5 inline-flex min-h-12 w-full items-center justify-center gap-2 rounded-xl bg-emerald-400 px-5 font-semibold text-slate-950 transition hover:bg-emerald-300 focus-visible:outline-2 focus-visible:outline-offset-4 disabled:cursor-wait disabled:opacity-60 sm:w-auto"
              >
                <Play size={18} fill="currentColor" />
                {running ? 'Guardian évalue…' : 'Lancer le scénario'}
              </motion.button>
              {apiError && <p role="alert" className="mt-3 text-sm text-rose-300">{apiError}</p>}
            </section>

            {/* Agent flow */}
            <section>
              <article className="rounded-2xl border border-white/8 bg-slate-950/55 p-4 sm:p-6">
                <div className="flex items-center justify-between gap-3 mb-4">
                  <div>
                    <p className="text-sm font-semibold text-white">Trace d'exécution 4 agents</p>
                    <p className="mt-1 text-xs text-slate-400">Chemin d'orchestration rapporté par le backend</p>
                  </div>
                  {result && (
                    <button
                      type="button"
                      onClick={() => setGraphOpen(true)}
                      className="flex items-center gap-2 rounded-lg border border-cyan-400/20 bg-cyan-400/[0.05] px-3 py-2 text-xs text-cyan-300 transition hover:bg-cyan-400/10"
                    >
                      <Activity size={15} /> Graphe d'exécution
                    </button>
                  )}
                </div>
                <AgentFlow activeAgent={activeAgent} running={running} stages={result?.agents} />
              </article>
            </section>

            {/* Metrics */}
            <section className="grid gap-4 md:grid-cols-3">
              {metrics.map((metric, i) => (
                <motion.article
                  key={metric.label}
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.08 }}
                  className="rounded-2xl border border-white/8 bg-slate-950/55 p-5"
                >
                  <div className="flex items-start justify-between">
                    <p className="text-sm text-slate-400">{metric.label}</p>
                    <CircleCheck size={17} className={metric.iconClass} />
                  </div>
                  <p className="mt-4 text-2xl font-semibold text-white">{metric.value}</p>
                </motion.article>
              ))}
            </section>

            {/* Forensic panel */}
            <section>
              <ForensicPanel phase={forensicPhase} result={result} running={running} />
            </section>
          </div>
        )}

        <footer className="mt-10 border-t border-white/6 py-6 text-center text-xs text-slate-400">
          ARTCB TERMINATOR · Guardian Security Console · Hackathon ESSEC 2026
        </footer>
      </div>

      {/* ── Execution graph modal ─────────────────────────────────────────── */}
      {graphOpen && (
        <Suspense fallback={
          <div className="fixed inset-0 z-50 grid place-items-center bg-black/75 text-sm text-cyan-300">
            Chargement graphe…
          </div>
        }>
          <ExecutionGraphOverlay
            open
            result={result}
            activeAgent={activeAgent}
            onClose={() => setGraphOpen(false)}
          />
        </Suspense>
      )}
    </main>
  )
}

export default App

import { motion } from 'framer-motion'
import { Activity, ShieldCheck } from 'lucide-react'

function App() {
  return (
    <main className="relative grid min-h-screen place-items-center overflow-hidden bg-[#050a12] px-6">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_50%_30%,rgba(16,185,129,0.12),transparent_38%)]" />
      <motion.section
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        className="relative w-full max-w-3xl rounded-3xl border border-white/10 bg-slate-950/70 p-8 text-center shadow-2xl shadow-emerald-950/30 backdrop-blur md:p-14"
      >
        <div className="mx-auto mb-6 flex size-16 items-center justify-center rounded-2xl border border-emerald-400/30 bg-emerald-400/10 text-emerald-300">
          <ShieldCheck size={34} aria-hidden="true" />
        </div>
        <p className="mb-3 font-mono text-xs font-semibold tracking-[0.28em] text-emerald-300 uppercase">
          Guardian Security Console
        </p>
        <h1 className="text-4xl font-semibold tracking-tight text-white md:text-6xl">
          ARTCB TERMINATOR
        </h1>
        <p className="mx-auto mt-5 max-w-xl text-base leading-7 text-slate-400 md:text-lg">
          Monitor AI agents, block dangerous tool actions, preserve evidence,
          and replay incidents safely.
        </p>
        <div className="mt-9 inline-flex items-center gap-2 rounded-full border border-emerald-400/20 bg-emerald-400/5 px-4 py-2 text-sm text-emerald-200">
          <Activity size={16} aria-hidden="true" />
          Guardian engine ready
        </div>
      </motion.section>
    </main>
  )
}

export default App

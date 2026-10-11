/**
 * KycPanel — ARTCB TERMINATOR FORENSIC
 * Scénario KYC complet jury-grade :
 *  1. Formulaire identité
 *  2. Traitement Guardian (attaque LLM détectée + contrée)
 *  3. PDF résultat avec taux de succès
 *  4. Timeline forensic en temps réel via SSE
 */
import { useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import {
  FileText, Shield, AlertTriangle, CheckCircle2,
  Clock, Download, User, Hash, Lock, Zap,
} from 'lucide-react'
import type { KycResult, KycStreamEvent } from '../api/guardian'

type KycPanelProps = {
  apiBase: string
}

type TimelineEntry = {
  id: string
  ts: number
  type: 'session' | 'attack' | 'block' | 'chain' | 'kyc_step' | 'done' | 'error'
  label: string
  detail: string
  status: 'ok' | 'warn' | 'fail' | 'info'
}

const TYPE_COLORS: Record<TimelineEntry['type'], string> = {
  session:  'text-cyan-300   border-cyan-400/40   bg-cyan-400/10',
  attack:   'text-amber-300  border-amber-400/40  bg-amber-400/10',
  block:    'text-emerald-300 border-emerald-400/40 bg-emerald-400/10',
  chain:    'text-violet-300 border-violet-400/40  bg-violet-400/10',
  kyc_step: 'text-sky-300    border-sky-400/40    bg-sky-400/10',
  done:     'text-emerald-300 border-emerald-400/50 bg-emerald-400/15',
  error:    'text-rose-300   border-rose-400/40   bg-rose-400/10',
}

const STATUS_ICON: Record<TimelineEntry['status'], React.ReactNode> = {
  ok:   <CheckCircle2 size={13} className="text-emerald-300 shrink-0" />,
  warn: <AlertTriangle size={13} className="text-amber-300 shrink-0" />,
  fail: <AlertTriangle size={13} className="text-rose-300 shrink-0" />,
  info: <Clock size={13} className="text-sky-300 shrink-0" />,
}

export function KycPanel({ apiBase }: KycPanelProps) {
  const [firstName, setFirstName] = useState('Alice')
  const [lastName,  setLastName]  = useState('Dupont')
  const [docId,     setDocId]     = useState('FR-2024-887634')
  const [dob,       setDob]       = useState('1990-05-14')

  const [running,   setRunning]   = useState(false)
  const [timeline,  setTimeline]  = useState<TimelineEntry[]>([])
  const [result,    setResult]    = useState<KycResult | null>(null)
  const [pdfUrl,    setPdfUrl]    = useState<string | null>(null)
  const [attackCount, setAttackCount] = useState(0)
  const [blockCount,  setBlockCount]  = useState(0)

  const timelineRef = useRef<HTMLDivElement>(null)
  const esRef       = useRef<EventSource | null>(null)

  // Auto-scroll timeline
  useEffect(() => {
    if (timelineRef.current) {
      timelineRef.current.scrollTop = timelineRef.current.scrollHeight
    }
  }, [timeline])

  function addEntry(entry: Omit<TimelineEntry, 'id' | 'ts'>) {
    setTimeline(prev => [...prev, { ...entry, id: crypto.randomUUID(), ts: Date.now() }])
  }

  function reset() {
    esRef.current?.close()
    setTimeline([])
    setResult(null)
    setPdfUrl(null)
    setAttackCount(0)
    setBlockCount(0)
  }

  async function runKyc() {
    reset()
    setRunning(true)

    addEntry({ type: 'kyc_step', label: 'KYC initialisé', detail: `Identité : ${firstName} ${lastName} | Doc : ${docId}`, status: 'info' })

    const es = new EventSource(`${apiBase}/api/kyc/stream?first_name=${encodeURIComponent(firstName)}&last_name=${encodeURIComponent(lastName)}&doc_id=${encodeURIComponent(docId)}&dob=${encodeURIComponent(dob)}`)
    esRef.current = es

    // Helper — dispatch vers App pour le HUD graph
    function dispatch(type: string, data: KycStreamEvent) {
      window.dispatchEvent(new CustomEvent('kyc_sse_event', { detail: { ...data, _type: type } }))
    }

    es.addEventListener('session_opened', (e: MessageEvent) => {
      const d = JSON.parse(e.data) as KycStreamEvent
      dispatch('session_opened', d)
      addEntry({ type: 'session',  label: 'Session Guardian ouverte', detail: `session: ${(d as Record<string, string>).session_id?.slice(0, 16)}…`, status: 'info' })
    })

    es.addEventListener('kyc_identity_check', (e: MessageEvent) => {
      const d = JSON.parse(e.data) as Record<string, string>
      dispatch('kyc_identity_check', d as KycStreamEvent)
      addEntry({ type: 'kyc_step', label: 'Vérification identité', detail: d.detail ?? 'Documents validés', status: 'ok' })
    })

    es.addEventListener('attack_generated', (e: MessageEvent) => {
      const d = JSON.parse(e.data) as Record<string, string>
      dispatch('attack_generated', d as KycStreamEvent)
      setAttackCount(c => c + 1)
      addEntry({ type: 'attack', label: `Attaque LLM détectée — ${d.tool_chosen}`, detail: `Modèle: ${d.model} | Args: ${JSON.stringify(d.arguments ?? {}).slice(0, 60)}`, status: 'warn' })
    })

    es.addEventListener('propagation', (e: MessageEvent) => {
      const d = JSON.parse(e.data) as Record<string, string>
      dispatch('propagation', d as KycStreamEvent)
      addEntry({ type: 'kyc_step', label: 'Propagation → Defender', detail: `${d.propagation_id?.slice(0, 16) ?? ''}…`, status: 'info' })
    })

    es.addEventListener('guardian_decision', (e: MessageEvent) => {
      const d = JSON.parse(e.data) as Record<string, string>
      dispatch('guardian_decision', d as KycStreamEvent)
      const blocked = d.decision === 'BLOCK'
      if (blocked) setBlockCount(c => c + 1)
      addEntry({
        type:   blocked ? 'block' : 'kyc_step',
        label:  `Guardian → ${d.decision}`,
        detail: d.reason ?? '',
        status: blocked ? 'ok' : 'warn',
      })
    })

    es.addEventListener('chain_verified', (e: MessageEvent) => {
      const d = JSON.parse(e.data) as Record<string, string>
      dispatch('chain_verified', d as KycStreamEvent)
      addEntry({ type: 'chain', label: `Chaîne cryptographique R0 — ${d.verdict}`, detail: `${d.events_replayed} événements vérifiés`, status: d.verdict === 'PASS' ? 'ok' : 'fail' })
    })

    es.addEventListener('kyc_result', (e: MessageEvent) => {
      const d = JSON.parse(e.data) as KycResult
      dispatch('kyc_result', d as unknown as KycStreamEvent)
      setResult(d)
      addEntry({ type: 'done', label: `KYC ${d.verdict}`, detail: `Score: ${d.score}% | Attaques bloquées: ${d.attacks_blocked}`, status: d.verdict === 'APPROVED' ? 'ok' : 'fail' })
    })

    es.addEventListener('done', (e: MessageEvent) => {
      const d = JSON.parse(e.data) as Record<string, unknown>
      dispatch('done', d as KycStreamEvent)
      if (d.pdf_b64) {
        const blob = new Blob([Uint8Array.from(atob(d.pdf_b64 as string), c => c.charCodeAt(0))], { type: 'application/pdf' })
        setPdfUrl(URL.createObjectURL(blob))
      }
      es.close()
      setRunning(false)
    })

    es.addEventListener('error', () => {
      addEntry({ type: 'error', label: 'Erreur stream', detail: 'Connexion SSE interrompue', status: 'fail' })
      es.close()
      setRunning(false)
    })
  }

  const successRate = attackCount > 0 ? Math.round((blockCount / attackCount) * 100) : 100

  return (
    <div className="rounded-2xl border border-white/8 bg-slate-950/70 overflow-hidden">
      {/* Header */}
      <div className="flex items-center gap-3 border-b border-white/8 px-5 py-4">
        <div className="flex size-9 items-center justify-center rounded-lg border border-emerald-400/25 bg-emerald-400/10">
          <User size={18} className="text-emerald-300" />
        </div>
        <div>
          <p className="font-semibold text-white text-sm">Scénario KYC — Know Your Customer</p>
          <p className="text-[11px] text-slate-500">Traitement identité en temps réel · attaques détectées · rapport PDF</p>
        </div>
        {result && (
          <span className={`ml-auto px-3 py-1 rounded-full text-xs font-bold border ${result.verdict === 'APPROVED' ? 'border-emerald-400/40 bg-emerald-400/10 text-emerald-300' : 'border-rose-400/40 bg-rose-400/10 text-rose-300'}`}>
            {result.verdict}
          </span>
        )}
      </div>

      <div className="grid lg:grid-cols-2 gap-0 divide-x divide-white/8 items-start">
        {/* LEFT — formulaire + métriques */}
        <div className="p-5 space-y-5 overflow-hidden">
          {/* Identité */}
          <div className="grid grid-cols-2 gap-3">
            {[
              { label: 'Prénom', value: firstName, set: setFirstName, icon: <User size={13}/> },
              { label: 'Nom',    value: lastName,  set: setLastName,  icon: <User size={13}/> },
              { label: 'N° Document', value: docId, set: setDocId, icon: <Hash size={13}/> },
              { label: 'Date naissance', value: dob, set: setDob,   icon: <FileText size={13}/> },
            ].map(field => (
              <label key={field.label} className="block space-y-1">
                <span className="flex items-center gap-1 text-[10px] font-semibold text-slate-500 uppercase tracking-wider">
                  {field.icon} {field.label}
                </span>
                <input
                  type="text"
                  value={field.value}
                  onChange={e => field.set(e.target.value)}
                  disabled={running}
                  className="w-full rounded-lg border border-white/10 bg-slate-900/60 px-3 py-2 text-sm text-white placeholder:text-slate-600 focus:border-cyan-400/40 focus:outline-none disabled:opacity-50"
                />
              </label>
            ))}
          </div>

          {/* Métriques */}
          <div className="grid grid-cols-3 gap-2">
            {[
              { label: 'Attaques', value: attackCount, icon: <Zap size={14} className="text-amber-300"/>, color: 'text-amber-300' },
              { label: 'Bloquées', value: blockCount,  icon: <Shield size={14} className="text-emerald-300"/>, color: 'text-emerald-300' },
              { label: 'Taux',     value: `${successRate}%`, icon: <Lock size={14} className="text-violet-300"/>, color: 'text-violet-300' },
            ].map(m => (
              <div key={m.label} className="rounded-xl border border-white/8 bg-slate-900/50 p-3 text-center">
                <div className="flex justify-center mb-1">{m.icon}</div>
                <p className={`text-xl font-bold ${m.color}`}>{m.value}</p>
                <p className="text-[10px] text-slate-500 mt-0.5">{m.label}</p>
              </div>
            ))}
          </div>

          {/* Boutons */}
          <div className="flex gap-2">
            <motion.button
              type="button"
              onClick={runKyc}
              disabled={running}
              whileHover={{ y: -1 }}
              whileTap={{ scale: 0.97 }}
              className="flex-1 flex items-center justify-center gap-2 rounded-xl bg-emerald-400 px-4 py-3 font-semibold text-slate-950 text-sm transition hover:bg-emerald-300 disabled:opacity-50 disabled:cursor-wait"
            >
              <Shield size={16} fill="currentColor" />
              {running ? 'Traitement KYC…' : 'Lancer KYC complet'}
            </motion.button>

            {pdfUrl && (
              <motion.a
                href={pdfUrl}
                download={`kyc-${firstName}-${lastName}.pdf`}
                whileHover={{ y: -1 }}
                className="flex items-center gap-2 rounded-xl border border-emerald-400/30 bg-emerald-400/10 px-4 py-3 text-emerald-300 text-sm font-semibold hover:bg-emerald-400/15 transition"
              >
                <Download size={15} /> Rapport PDF
              </motion.a>
            )}
          </div>

          {/* Résultat KYC */}
          {result && (
            <div className={`rounded-xl border p-4 ${result.verdict === 'APPROVED' ? 'border-emerald-400/30 bg-emerald-400/5' : 'border-rose-400/30 bg-rose-400/5'}`}>
              <p className="text-xs text-slate-400 uppercase tracking-wider mb-2 font-semibold">Rapport KYC</p>
              <div className="grid grid-cols-2 gap-2 text-xs">
                {[
                  ['Verdict', result.verdict],
                  ['Score',   `${result.score}%`],
                  ['Attaques bloquées', String(result.attacks_blocked)],
                  ['Chaîne intègre',   result.chain_intact ? 'OUI' : 'NON'],
                  ['Session',  result.session_id.slice(0, 14) + '…'],
                  ['Timestamp', new Date(result.timestamp).toLocaleTimeString()],
                ].map(([k, v]) => (
                  <div key={k} className="flex justify-between gap-1">
                    <span className="text-slate-500">{k}</span>
                    <span className="font-mono text-white">{v}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* RIGHT — timeline forensic */}
        <div className="p-5 flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Timeline Forensic</p>
            {running && <span className="flex items-center gap-1.5 text-[10px] text-cyan-300 animate-pulse"><span className="size-1.5 rounded-full bg-cyan-400 inline-block"/>LIVE</span>}
          </div>

          <div ref={timelineRef} className="h-[360px] overflow-y-auto space-y-1.5 pr-1">
            {timeline.length === 0 ? (
              <p className="text-xs text-slate-600 text-center py-10">Lance un scénario KYC pour voir les événements forensic en temps réel</p>
            ) : (
              timeline.map(entry => (
                <motion.div
                  key={entry.id}
                  initial={{ opacity: 0, x: 8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.18 }}
                  className={`flex items-start gap-2 rounded-lg border px-3 py-2 ${TYPE_COLORS[entry.type]}`}
                >
                  {STATUS_ICON[entry.status]}
                  <div className="min-w-0 flex-1">
                    <p className="text-[11px] font-semibold leading-tight">{entry.label}</p>
                    {entry.detail && <p className="text-[10px] opacity-70 mt-0.5 font-mono truncate">{entry.detail}</p>}
                  </div>
                  <span className="text-[9px] opacity-50 shrink-0 font-mono">{new Date(entry.ts).toLocaleTimeString()}</span>
                </motion.div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

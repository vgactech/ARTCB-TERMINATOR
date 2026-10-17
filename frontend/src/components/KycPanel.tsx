/**
 * KycPanel — ARTCB TERMINATOR FORENSIC
 * Robuste mobile + desktop, sans AnimatePresence, sans overflow-hidden
 *
 * R084 — PII hors URL : EventSource GET → fetch POST SSE manuel.
 * Les données personnelles (prénom, nom, docId, dob) ne transitent plus
 * jamais dans l'URL (et donc dans les logs Nginx / access logs).
 * On utilise fetch() + ReadableStream pour consommer le flux text/event-stream.
 *
 * R087 — F086-01 : ajout du case kyc_validation_check dans handleEvent.
 * R087 — F086-02 : nom PDF sûr (session_id court, pas PII) + revoke Blob URL.
 * R087 — F086-03 : curEvent/curData déclarés hors du while(true) pour
 *                  corriger le bug de chunk-boundary SSE.
 */
import { useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import {
  Shield, AlertTriangle, CheckCircle2,
  Clock, Download, User,
} from 'lucide-react'
import type { KycResult, KycStreamEvent } from '../api/guardian'

type KycPanelProps = { apiBase: string }

type TimelineEntry = {
  id: string
  ts: number
  type: 'session' | 'attack' | 'block' | 'chain' | 'kyc_step' | 'done' | 'error'
  label: string
  detail: string
  status: 'ok' | 'warn' | 'fail' | 'info'
}

const TYPE_BG: Record<TimelineEntry['type'], string> = {
  session:  'border-l-cyan-400   bg-cyan-950/40',
  attack:   'border-l-amber-400  bg-amber-950/40',
  block:    'border-l-emerald-400 bg-emerald-950/40',
  chain:    'border-l-violet-400  bg-violet-950/40',
  kyc_step: 'border-l-sky-400    bg-sky-950/40',
  done:     'border-l-emerald-400 bg-emerald-950/60',
  error:    'border-l-rose-400    bg-rose-950/40',
}

const TYPE_TEXT: Record<TimelineEntry['type'], string> = {
  session:  'text-cyan-300',
  attack:   'text-amber-300',
  block:    'text-emerald-300',
  chain:    'text-violet-300',
  kyc_step: 'text-sky-300',
  done:     'text-emerald-300',
  error:    'text-rose-300',
}

function StatusDot({ status }: { status: TimelineEntry['status'] }) {
  if (status === 'ok')   return <CheckCircle2 size={12} className="text-emerald-400 shrink-0 mt-0.5" />
  if (status === 'warn') return <AlertTriangle size={12} className="text-amber-400 shrink-0 mt-0.5" />
  if (status === 'fail') return <AlertTriangle size={12} className="text-rose-400 shrink-0 mt-0.5" />
  return <Clock size={12} className="text-sky-400 shrink-0 mt-0.5" />
}

export function KycPanel({ apiBase }: KycPanelProps) {
  const [firstName, setFirstName] = useState('Alice')
  const [lastName,  setLastName]  = useState('Dupont')
  const [docId,     setDocId]     = useState('FR-2024-887634')
  const [dob,       setDob]       = useState('1990-05-14')
  const [running,   setRunning]   = useState(false)
  const [sessionId, setSessionId] = useState<string>('')
  const [timeline,  setTimeline]  = useState<TimelineEntry[]>([])
  const [result,    setResult]    = useState<KycResult | null>(null)
  const [pdfUrl,    setPdfUrl]    = useState<string | null>(null)
  const [attackCount, setAttackCount] = useState(0)
  const [blockCount,  setBlockCount]  = useState(0)
  const timelineRef = useRef<HTMLDivElement>(null)
  const esRef       = useRef<AbortController | null>(null)

  useEffect(() => {
    if (timelineRef.current)
      timelineRef.current.scrollTop = timelineRef.current.scrollHeight
  }, [timeline])

  function addEntry(e: Omit<TimelineEntry, 'id' | 'ts'>) {
    setTimeline(prev => [...prev, { ...e, id: crypto.randomUUID(), ts: Date.now() }])
  }

  function dispatch(type: string, data: KycStreamEvent) {
    window.dispatchEvent(new CustomEvent('kyc_sse_event', { detail: { ...data, _type: type } }))
  }

  function reset() {
    esRef.current?.abort()
    setTimeline([])
    setResult(null)
    // F086-02 — revoke Blob URL pour libérer la mémoire avant de la réinitialiser
    setPdfUrl(prev => { if (prev) URL.revokeObjectURL(prev); return null })
    setAttackCount(0)
    setBlockCount(0)
    setSessionId('')
  }

  function runKyc() {
    // Validation : refuser la soumission si un champ requis est vide
    if (!firstName.trim() || !lastName.trim() || !docId.trim() || !dob.trim()) {
      addEntry({ type: 'error', label: 'Champ requis manquant', detail: 'Prénom, nom, n° document et date de naissance sont obligatoires', status: 'fail' })
      return
    }
    reset()
    setRunning(true)
    addEntry({ type: 'kyc_step', label: 'KYC initialisé', detail: `${firstName || '?'} ${lastName || '?'} · ${docId || '?'}`, status: 'info' })

    // R084 — PII hors URL : POST body JSON + SSE manuel via fetch().
    // EventSource n'est pas utilisé : il ne supporte que GET (PII dans l'URL → logs Nginx).
    // On ouvre un POST vers /api/kyc/stream avec les données dans le body.
    // Le backend répond avec Content-Type: text/event-stream — on lit le ReadableStream.
    const ctrl = new AbortController()
    esRef.current = ctrl

    ;(async () => {
      try {
        const resp = await fetch(`${apiBase}/api/kyc/stream`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
          body: JSON.stringify({ first_name: firstName, last_name: lastName, doc_id: docId, dob }),
          signal: ctrl.signal,
        })

        if (!resp.ok || !resp.body) {
          addEntry({ type: 'error', label: 'Erreur connexion SSE', detail: `HTTP ${resp.status} — vérifier VITE_API_URL`, status: 'fail' })
          setRunning(false)
          return
        }

        const reader = resp.body.getReader()
        const decoder = new TextDecoder()
        let buf = ''

        // Parseur SSE minimal : accumule les lignes, dispatch sur ligne vide
        const handleEvent = (eventType: string, rawData: string) => {
          try {
            const d = JSON.parse(rawData) as Record<string, unknown>
            switch (eventType) {
              case 'session_opened':
                dispatch('session_opened', d as KycStreamEvent)
                // F086-02 — capturer session_id pour construire le nom de fichier PDF
                setSessionId((d.session_id as string) ?? '')
                addEntry({ type: 'session', label: 'Session Guardian ouverte', detail: `sess: ${(d.session_id as string)?.slice(0, 20)}…`, status: 'info' })
                break
              case 'kyc_identity_check':
                dispatch('kyc_identity_check', d as KycStreamEvent)
                addEntry({ type: 'kyc_step', label: `Identité ${d.status === 'PASS' ? 'validée ✓' : 'refusée ✗'}`, detail: (d.detail as string) ?? '', status: d.status === 'PASS' ? 'ok' : 'fail' })
                break
              // F086-01 — event kyc_validation_check (S1b) ajouté
              case 'kyc_validation_check':
                dispatch('kyc_validation_check', d as KycStreamEvent)
                addEntry({ type: 'kyc_step', label: `Validation doc ${d.status === 'PASS' ? '✓' : '✗'}`, detail: (d.detail as string) ?? '', status: d.status === 'PASS' ? 'ok' : 'fail' })
                break
              case 'attack_generated':
                dispatch('attack_generated', d as KycStreamEvent)
                setAttackCount(c => c + 1)
                addEntry({ type: 'attack', label: `⚠ Attaque LLM → ${d.tool_chosen}`, detail: `args: ${JSON.stringify(d.arguments ?? {}).slice(0, 55)}`, status: 'warn' })
                break
              case 'propagation':
                dispatch('propagation', d as KycStreamEvent)
                addEntry({ type: 'kyc_step', label: 'Propagation → Guardian', detail: `prop: ${(d.propagation_id as string)?.slice(0, 20) ?? ''}…`, status: 'info' })
                break
              case 'guardian_decision': {
                dispatch('guardian_decision', d as KycStreamEvent)
                const blocked = d.decision === 'BLOCK'
                if (blocked) setBlockCount(c => c + 1)
                addEntry({ type: blocked ? 'block' : 'kyc_step', label: `Guardian → ${d.decision}`, detail: (d.reason as string) ?? '', status: blocked ? 'ok' : 'warn' })
                break
              }
              case 'chain_verified':
                dispatch('chain_verified', d as KycStreamEvent)
                addEntry({ type: 'chain', label: `Chaîne R0 → ${d.verdict}`, detail: `${d.events_replayed} événements vérifiés`, status: d.verdict === 'PASS' ? 'ok' : 'fail' })
                break
              case 'kyc_result': {
                const r = d as unknown as KycResult
                dispatch('kyc_result', d as KycStreamEvent)
                setResult(r)
                addEntry({ type: 'done', label: `KYC ${r.verdict} · Score ${r.score}%`, detail: `${r.attacks_blocked} attaque(s) bloquée(s) · chaîne ${r.chain_intact ? 'intacte' : 'compromise'}`, status: r.verdict === 'APPROVED' ? 'ok' : 'fail' })
                break
              }
              case 'done':
                dispatch('done', d as KycStreamEvent)
                if (d.pdf_b64) {
                  const blob = new Blob([Uint8Array.from(atob(d.pdf_b64 as string), c => c.charCodeAt(0))], { type: 'application/pdf' })
                  setPdfUrl(URL.createObjectURL(blob))
                }
                setRunning(false)
                break
              default:
                break
            }
          } catch {
            // JSON parse error — ignorer silencieusement
          }
        }

        // Lecture du flux ligne par ligne
        // F086-03 — curEvent/curData déclarés HORS du while pour survivre
        //           aux coupures de chunk réseau (bug chunk-boundary SSE)
        let curEvent = 'message'
        let curData = ''
        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          buf += decoder.decode(value, { stream: true })
          const lines = buf.split('\n')
          buf = lines.pop() ?? ''
          for (const line of lines) {
            if (line.startsWith('event:')) {
              curEvent = line.slice(6).trim()
            } else if (line.startsWith('data:')) {
              curData = line.slice(5).trim()
            } else if (line === '' && curData) {
              handleEvent(curEvent, curData)
              curEvent = 'message'
              curData = ''
            }
          }
        }
        setRunning(false)
      } catch (err) {
        if ((err as Error).name === 'AbortError') return // reset() appelé — normal
        addEntry({
          type: 'error',
          label: 'Erreur connexion SSE',
          detail: `API inaccessible (${apiBase || 'URL non configurée'}) — vérifier VITE_API_URL`,
          status: 'fail',
        })
        setRunning(false)
      }
    })()
  }

  const successRate = attackCount > 0 ? Math.round((blockCount / attackCount) * 100) : 100

  // ── Render ─────────────────────────────────────────────────────────────────
  return (
    <div style={{ background: '#0b1321', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 16 }}>

      {/* ── Header ──────────────────────────────────────────────────────── */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '16px 20px', borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
        <div style={{ width: 36, height: 36, borderRadius: 10, background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.25)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <User size={17} color="#6ee7b7" />
        </div>
        <div style={{ flex: 1 }}>
          <p style={{ margin: 0, fontSize: 13, fontWeight: 700, color: '#fff' }}>Scénario KYC — Know Your Customer</p>
          <p style={{ margin: 0, fontSize: 11, color: '#64748b' }}>Traitement identité · attaque LLM · Guardian · rapport PDF</p>
        </div>
        {result && (
          <span style={{
            padding: '3px 10px', borderRadius: 20, fontSize: 11, fontWeight: 700,
            background: result.verdict === 'APPROVED' ? 'rgba(16,185,129,0.12)' : 'rgba(244,63,94,0.12)',
            border: `1px solid ${result.verdict === 'APPROVED' ? 'rgba(16,185,129,0.4)' : 'rgba(244,63,94,0.4)'}`,
            color: result.verdict === 'APPROVED' ? '#6ee7b7' : '#fda4af',
          }}>{result.verdict}</span>
        )}
      </div>

      {/* ── Body : 2 colonnes sur large, 1 sur mobile ───────────────────── */}
      <div style={{ display: 'flex', flexWrap: 'wrap' }}>

        {/* ─ Colonne gauche : formulaire ─────────────────────────────────── */}
        <div style={{ flex: '1 1 320px', padding: 20, display: 'flex', flexDirection: 'column', gap: 16, borderRight: '1px solid rgba(255,255,255,0.06)' }}>

          {/* Champs identité */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            {[
              { label: 'Prénom',          value: firstName, set: setFirstName },
              { label: 'Nom',             value: lastName,  set: setLastName  },
              { label: 'N° Document',     value: docId,     set: setDocId     },
              { label: 'Date naissance',  value: dob,       set: setDob       },
            ].map(f => (
              <label key={f.label} style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                <span style={{ fontSize: 10, fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.08em' }}>{f.label}</span>
                <input
                  type="text"
                  value={f.value}
                  onChange={e => f.set(e.target.value)}
                  disabled={running}
                  style={{
                    background: 'rgba(15,23,42,0.7)', border: '1px solid rgba(255,255,255,0.1)',
                    borderRadius: 8, padding: '7px 10px', fontSize: 13, color: '#fff',
                    outline: 'none', opacity: running ? 0.5 : 1,
                  }}
                />
              </label>
            ))}
          </div>

          {/* Métriques */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 8 }}>
            {[
              { label: 'Attaques', value: attackCount, color: '#fbbf24' },
              { label: 'Bloquées', value: blockCount,  color: '#34d399' },
              { label: 'Taux',     value: `${successRate}%`, color: '#a78bfa' },
            ].map(m => (
              <div key={m.label} style={{ background: 'rgba(15,23,42,0.6)', border: '1px solid rgba(255,255,255,0.06)', borderRadius: 10, padding: '10px 8px', textAlign: 'center' }}>
                <p style={{ margin: 0, fontSize: 20, fontWeight: 700, color: m.color }}>{m.value}</p>
                <p style={{ margin: '2px 0 0', fontSize: 10, color: '#94a3b8' }}>{m.label}</p>
              </div>
            ))}
          </div>

          {/* Boutons */}
          <div style={{ display: 'flex', gap: 8 }}>
            <motion.button
              whileHover={{ y: -1 }}
              whileTap={{ scale: 0.97 }}
              onClick={runKyc}
              disabled={running}
              style={{
                flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                background: running ? '#14532d' : '#34d399', color: '#0b1321',
                border: 'none', borderRadius: 12, padding: '12px 16px',
                fontSize: 14, fontWeight: 700, cursor: running ? 'wait' : 'pointer',
                opacity: running ? 0.7 : 1,
              }}
            >
              <Shield size={15} fill="currentColor" />
              {running ? 'Traitement KYC…' : 'Lancer KYC complet'}
            </motion.button>

            {pdfUrl && (
              <a
                href={pdfUrl}
                download={`artcb-kyc-report-${sessionId ? sessionId.slice(0, 12) : 'session'}.pdf`}
                style={{
                  display: 'flex', alignItems: 'center', gap: 6, padding: '12px 14px',
                  background: 'rgba(16,185,129,0.1)', border: '1px solid rgba(16,185,129,0.3)',
                  borderRadius: 12, color: '#6ee7b7', fontSize: 13, fontWeight: 600,
                  textDecoration: 'none',
                }}
              >
                <Download size={14} /> PDF
              </a>
            )}
          </div>

          {/* Résultat KYC */}
          {result && (
            <div style={{
              background: result.verdict === 'APPROVED' ? 'rgba(16,185,129,0.05)' : 'rgba(244,63,94,0.05)',
              border: `1px solid ${result.verdict === 'APPROVED' ? 'rgba(16,185,129,0.25)' : 'rgba(244,63,94,0.25)'}`,
              borderRadius: 12, padding: 14,
            }}>
              <p style={{ margin: '0 0 8px', fontSize: 10, fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Rapport KYC</p>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '4px 8px' }}>
                {[
                  ['Verdict',           result.verdict],
                  ['Score',             `${result.score}%`],
                  ['Attaques bloquées', String(result.attacks_blocked)],
                  ['Chaîne intègre',    result.chain_intact ? 'OUI' : 'NON'],
                  ['Session',           result.session_id.slice(0, 12) + '…'],
                  ['Heure',             new Date(result.timestamp).toLocaleTimeString()],
                ].map(([k, v]) => (
                  <div key={k} style={{ display: 'flex', justifyContent: 'space-between', gap: 4, fontSize: 11 }}>
                    <span style={{ color: '#64748b' }}>{k}</span>
                    <span style={{ color: '#f1f5f9', fontFamily: 'monospace' }}>{v}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* ─ Colonne droite : timeline forensic ────────────────────────── */}
        <div style={{ flex: '1 1 320px', padding: 20, display: 'flex', flexDirection: 'column', gap: 10 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <p style={{ margin: 0, fontSize: 11, fontWeight: 600, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.1em' }}>Timeline Forensic</p>
            {running && (
              <span style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 10, color: '#22d3ee' }}>
                <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#22d3ee', display: 'inline-block', animation: 'pulse 1s infinite' }} />
                LIVE
              </span>
            )}
          </div>

          <div
            ref={timelineRef}
            style={{ height: 340, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 6 }}
          >
            {timeline.length === 0 ? (
              <p style={{ textAlign: 'center', color: '#334155', fontSize: 12, marginTop: 60 }}>
                Lance un scénario KYC pour voir les événements en temps réel
              </p>
            ) : (
              timeline.map(entry => (
                <motion.div
                  key={entry.id}
                  initial={{ opacity: 0, x: 10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.15 }}
                  className={`border-l-2 ${TYPE_BG[entry.type]}`}
                  style={{ borderRadius: '0 8px 8px 0', padding: '7px 10px', display: 'flex', alignItems: 'flex-start', gap: 7 }}
                >
                  <StatusDot status={entry.status} />
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <p style={{ margin: 0, fontSize: 11, fontWeight: 600, lineHeight: 1.3 }} className={TYPE_TEXT[entry.type]}>
                      {entry.label}
                    </p>
                    {entry.detail && (
                      <p style={{ margin: '2px 0 0', fontSize: 10, color: '#64748b', fontFamily: 'monospace', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                        {entry.detail}
                      </p>
                    )}
                  </div>
                  <span style={{ fontSize: 9, color: '#334155', fontFamily: 'monospace', flexShrink: 0 }}>
                    {new Date(entry.ts).toLocaleTimeString()}
                  </span>
                </motion.div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

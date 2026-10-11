/**
 * AnimatedArchitectureGraph — ARTCB TERMINATOR FORENSIC
 *
 * Graphe d'architecture animé inspiré du diagramme "AI Agent Architecture"
 * Flux de traitement : Input → Understanding → Reasoning → Guardian → Preuve → Rapport
 * Style : SVG inline, dark navy, flèches pointillées animées, nœuds avec pulse
 */
import { useEffect, useRef, useState } from 'react'
import { motion } from 'framer-motion'

// ─── Types ────────────────────────────────────────────────────────────────────

type NodeId =
  | 'input'
  | 'understanding'
  | 'reasoning'
  | 'goal_check'
  | 'memory'
  | 'respond_direct'
  | 'output_direct'
  | 'action_tool'
  | 'planning'
  | 'mcp'
  | 'monitoring'
  | 'safety'
  | 'guardian_block'
  | 'proof'

type NodeDef = {
  id: NodeId
  label: string
  sub?: string
  x: number
  y: number
  w: number
  h: number
  shape: 'rect' | 'diamond' | 'circle'
  color: 'amber' | 'cyan' | 'emerald' | 'violet' | 'rose' | 'sky' | 'red'
}

type EdgeDef = {
  from: NodeId
  to: NodeId
  label?: string
  dashed?: boolean
  color?: string
  animated?: boolean
}

// ─── Layout (coordonnées dans un espace 900×600) ───────────────────────────

const NODES: NodeDef[] = [
  // Col 0 — Input
  { id: 'input',        label: 'Input',           sub: 'Requêtes · API · Events',  x: 30,  y: 220, w: 130, h: 64,  shape: 'rect',    color: 'amber'   },
  // Col 1 — Understanding
  { id: 'understanding',label: 'Understanding',   sub: 'Layer',                     x: 220, y: 60,  w: 140, h: 64,  shape: 'rect',    color: 'cyan'    },
  // Col 1 — Memory
  { id: 'memory',       label: 'Memory System',   sub: 'Court·Long terme',          x: 30,  y: 390, w: 130, h: 72,  shape: 'rect',    color: 'sky'     },
  // Col 2 — Reasoning
  { id: 'reasoning',    label: 'Reasoning Engine',sub: 'LLM · ReAct · CoT',         x: 420, y: 120, w: 160, h: 72,  shape: 'rect',    color: 'violet'  },
  // Col 2 — Can I respond?
  { id: 'respond_direct', label: 'Can I respond\ndirectly?', sub: '',               x: 310, y: 310, w: 110, h: 60,  shape: 'diamond', color: 'sky'     },
  // Col 2 — Goal check
  { id: 'goal_check',   label: 'Goal\ncompleted?', sub: '',                          x: 640, y: 120, w: 100, h: 60,  shape: 'diamond', color: 'cyan'    },
  // Direct output
  { id: 'output_direct',label: 'Output',           sub: 'Réponse directe',           x: 480, y: 310, w: 110, h: 54,  shape: 'rect',    color: 'emerald' },
  // Action / Tool
  { id: 'action_tool',  label: 'Action / Tool',   sub: 'Appel outil sensible',       x: 390, y: 430, w: 140, h: 62,  shape: 'rect',    color: 'amber'   },
  // Planning
  { id: 'planning',     label: 'Planning Module', sub: 'Step 1→2→3',                x: 660, y: 310, w: 130, h: 64,  shape: 'rect',    color: 'sky'     },
  // MCP
  { id: 'mcp',          label: 'MCP Bridge',      sub: 'File · API · DB · GitHub',  x: 580, y: 460, w: 140, h: 64,  shape: 'rect',    color: 'cyan'    },
  // Monitoring
  { id: 'monitoring',   label: 'Monitoring',      sub: 'Content · Rate · Human',    x: 100, y: 510, w: 130, h: 64,  shape: 'rect',    color: 'sky'     },
  // Safety
  { id: 'safety',       label: 'Safety & Controls', sub: 'Guardian Engine R0',      x: 270, y: 510, w: 150, h: 64,  shape: 'rect',    color: 'rose'    },
  // Guardian BLOCK
  { id: 'guardian_block', label: '🛡 GUARDIAN',   sub: 'BLOCK / ALLOW',             x: 420, y: 220, w: 130, h: 64,  shape: 'rect',    color: 'emerald' },
  // Proof
  { id: 'proof',        label: 'Preuve R0',       sub: 'SHA-256 · Chaîne',          x: 760, y: 430, w: 110, h: 62,  shape: 'rect',    color: 'violet'  },
]

const EDGES: EdgeDef[] = [
  { from: 'input',         to: 'understanding',   dashed: true,  color: 'cyan'    },
  { from: 'input',         to: 'memory',          dashed: true,  color: 'sky'     },
  { from: 'understanding', to: 'reasoning',       dashed: true,  color: 'violet'  },
  { from: 'reasoning',     to: 'goal_check',      label: '',     dashed: false, color: 'cyan'   },
  { from: 'goal_check',    to: 'planning',        label: 'No',   dashed: true,  color: 'amber'  },
  { from: 'reasoning',     to: 'respond_direct',  label: 'No',   dashed: true,  color: 'sky'    },
  { from: 'respond_direct',to: 'output_direct',   label: 'Yes',  dashed: false, color: 'emerald'},
  { from: 'respond_direct',to: 'action_tool',     label: 'No',   dashed: true,  color: 'amber'  },
  { from: 'action_tool',   to: 'guardian_block',  dashed: false, color: 'emerald', animated: true },
  { from: 'guardian_block',to: 'proof',           dashed: false, color: 'violet',  animated: true },
  { from: 'planning',      to: 'action_tool',     dashed: true,  color: 'amber'  },
  { from: 'action_tool',   to: 'mcp',             dashed: true,  color: 'cyan'   },
  { from: 'monitoring',    to: 'safety',          dashed: false, color: 'rose'   },
  { from: 'memory',        to: 'respond_direct',  dashed: true,  color: 'sky'    },
]

// ─── Utilitaires SVG ──────────────────────────────────────────────────────────

const COLOR_MAP: Record<string, { stroke: string; fill: string; text: string; glow: string }> = {
  amber:   { stroke: '#f59e0b', fill: 'rgba(245,158,11,0.08)',  text: '#fcd34d', glow: 'rgba(245,158,11,0.3)'  },
  cyan:    { stroke: '#22d3ee', fill: 'rgba(34,211,238,0.08)',  text: '#67e8f9', glow: 'rgba(34,211,238,0.3)'  },
  emerald: { stroke: '#34d399', fill: 'rgba(52,211,153,0.10)',  text: '#6ee7b7', glow: 'rgba(52,211,153,0.35)' },
  violet:  { stroke: '#a78bfa', fill: 'rgba(167,139,250,0.08)', text: '#c4b5fd', glow: 'rgba(167,139,250,0.3)' },
  rose:    { stroke: '#fb7185', fill: 'rgba(251,113,133,0.08)', text: '#fda4af', glow: 'rgba(251,113,133,0.3)' },
  sky:     { stroke: '#38bdf8', fill: 'rgba(56,189,248,0.08)',  text: '#7dd3fc', glow: 'rgba(56,189,248,0.3)'  },
  red:     { stroke: '#ef4444', fill: 'rgba(239,68,68,0.08)',   text: '#fca5a5', glow: 'rgba(239,68,68,0.3)'   },
}

function nodeCenter(n: NodeDef): [number, number] {
  return [n.x + n.w / 2, n.y + n.h / 2]
}

function getNodeById(id: NodeId): NodeDef {
  return NODES.find(n => n.id === id)!
}

// Calcule le point d'entrée/sortie d'un nœud vers une direction
function edgePort(n: NodeDef, direction: 'l' | 'r' | 't' | 'b'): [number, number] {
  const cx = n.x + n.w / 2
  const cy = n.y + n.h / 2
  if (direction === 'l') return [n.x, cy]
  if (direction === 'r') return [n.x + n.w, cy]
  if (direction === 't') return [cx, n.y]
  return [cx, n.y + n.h]
}

// Port auto-select based on relative position
function autoPort(from: NodeDef, to: NodeDef): { fp: [number, number]; tp: [number, number] } {
  const [fcx, fcy] = nodeCenter(from)
  const [tcx, tcy] = nodeCenter(to)
  const dx = tcx - fcx
  const dy = tcy - fcy
  let fDir: 'l' | 'r' | 't' | 'b'
  let tDir: 'l' | 'r' | 't' | 'b'
  if (Math.abs(dx) > Math.abs(dy)) {
    fDir = dx > 0 ? 'r' : 'l'
    tDir = dx > 0 ? 'l' : 'r'
  } else {
    fDir = dy > 0 ? 'b' : 't'
    tDir = dy > 0 ? 't' : 'b'
  }
  return { fp: edgePort(from, fDir), tp: edgePort(to, tDir) }
}

function cubicPath(fp: [number, number], tp: [number, number]): string {
  const dx = Math.abs(tp[0] - fp[0])
  const cx = dx * 0.45
  return `M ${fp[0]} ${fp[1]} C ${fp[0] + cx} ${fp[1]}, ${tp[0] - cx} ${tp[1]}, ${tp[0]} ${tp[1]}`
}

// ─── Composant nœud SVG ───────────────────────────────────────────────────────

function SvgNode({ node, active, pulse }: { node: NodeDef; active: boolean; pulse: boolean }) {
  const c = COLOR_MAP[node.color]
  const [cx, cy] = nodeCenter(node)
  const lines = node.label.split('\n')

  if (node.shape === 'diamond') {
    const hw = node.w / 2
    const hh = node.h / 2
    const pts = `${cx},${cy - hh} ${cx + hw},${cy} ${cx},${cy + hh} ${cx - hw},${cy}`
    return (
      <g>
        {pulse && (
          <polygon points={pts} fill="none" stroke={c.stroke} strokeWidth="1" opacity="0.4">
            <animate attributeName="stroke-width" values="1;3;1" dur="1.8s" repeatCount="indefinite" />
            <animate attributeName="opacity" values="0.4;0.1;0.4" dur="1.8s" repeatCount="indefinite" />
          </polygon>
        )}
        <polygon points={pts} fill={active ? c.fill : 'rgba(5,10,18,0.8)'} stroke={c.stroke} strokeWidth={active ? 1.5 : 1} />
        <text x={cx} y={cy + 1} textAnchor="middle" dominantBaseline="middle" fontSize="9" fontWeight="700" fill={c.text} fontFamily="monospace">
          {lines[0]}
        </text>
        {lines[1] && (
          <text x={cx} y={cy + 13} textAnchor="middle" dominantBaseline="middle" fontSize="9" fontWeight="700" fill={c.text} fontFamily="monospace">
            {lines[1]}
          </text>
        )}
      </g>
    )
  }

  return (
    <g>
      {pulse && (
        <rect x={node.x - 2} y={node.y - 2} width={node.w + 4} height={node.h + 4} rx="10" fill="none" stroke={c.stroke} strokeWidth="1" opacity="0.3">
          <animate attributeName="stroke-width" values="1;4;1" dur="2s" repeatCount="indefinite" />
          <animate attributeName="opacity" values="0.3;0;0.3" dur="2s" repeatCount="indefinite" />
        </rect>
      )}
      <rect x={node.x} y={node.y} width={node.w} height={node.h} rx="8"
        fill={active ? c.fill : 'rgba(5,10,18,0.85)'}
        stroke={c.stroke}
        strokeWidth={active ? 1.5 : 0.8}
      />
      {/* label lines */}
      {lines.map((line, i) => (
        <text key={i} x={cx} y={cy - (lines.length - 1) * 7 + i * 14 - (node.sub ? 6 : 0)}
          textAnchor="middle" dominantBaseline="middle"
          fontSize="10" fontWeight="700" fill={c.text} fontFamily="monospace">
          {line}
        </text>
      ))}
      {node.sub && (
        <text x={cx} y={cy + (lines.length) * 7 + (node.sub ? 2 : 0)}
          textAnchor="middle" dominantBaseline="middle"
          fontSize="8" fontWeight="400" fill={c.text} opacity="0.6" fontFamily="sans-serif">
          {node.sub}
        </text>
      )}
    </g>
  )
}

// ─── Composant edge SVG ───────────────────────────────────────────────────────

function SvgEdge({ edge, active }: { edge: EdgeDef; active: boolean }) {
  const fromNode = getNodeById(edge.from)
  const toNode   = getNodeById(edge.to)
  const { fp, tp } = autoPort(fromNode, toNode)
  const d = cubicPath(fp, tp)
  const col = edge.color ? COLOR_MAP[edge.color]?.stroke ?? '#94a3b8' : '#94a3b8'
  const midX = (fp[0] + tp[0]) / 2
  const midY = (fp[1] + tp[1]) / 2

  return (
    <g>
      <path d={d} fill="none" stroke={col}
        strokeWidth={active ? 2 : 0.8}
        strokeDasharray={edge.dashed ? '5 4' : undefined}
        opacity={active ? 1 : 0.35}
        markerEnd={`url(#arrow-${edge.color ?? 'default'})`}
      />
      {/* Particle animé sur les edges clés */}
      {edge.animated && active && (
        <circle r="3.5" fill={col} opacity="0.9">
          <animateMotion dur="1.6s" repeatCount="indefinite" path={d} />
        </circle>
      )}
      {edge.label && (
        <text x={midX} y={midY - 5} textAnchor="middle" fontSize="8" fill={col} fontFamily="monospace" fontWeight="600">
          {edge.label}
        </text>
      )}
    </g>
  )
}

// ─── Composant principal ──────────────────────────────────────────────────────

export function AnimatedArchitectureGraph() {
  const [step, setStep] = useState(0)
  const [running, setRunning] = useState(false)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Séquence d'animation : liste ordonnée de NodeId activés un par un
  const SEQUENCE: NodeId[] = [
    'input',
    'understanding',
    'memory',
    'reasoning',
    'goal_check',
    'respond_direct',
    'action_tool',
    'guardian_block',
    'proof',
    'monitoring',
    'safety',
    'mcp',
    'planning',
    'output_direct',
  ]

  const [activeNodes, setActiveNodes] = useState<Set<NodeId>>(new Set())
  const [activeEdges, setActiveEdges] = useState<Set<string>>(new Set())

  const edgeKey = (e: EdgeDef) => `${e.from}->${e.to}`

  function getEdgesFrom(nodeId: NodeId): EdgeDef[] {
    return EDGES.filter(e => e.from === nodeId)
  }

  function startAnimation() {
    setActiveNodes(new Set())
    setActiveEdges(new Set())
    setStep(0)
    setRunning(true)
  }

  useEffect(() => {
    if (!running) return
    if (step >= SEQUENCE.length) {
      // fin du cycle — pause puis reloop
      timerRef.current = setTimeout(() => {
        setRunning(false)
        setTimeout(startAnimation, 1200)
      }, 2000)
      return
    }
    timerRef.current = setTimeout(() => {
      const nodeId = SEQUENCE[step]
      setActiveNodes(prev => new Set([...prev, nodeId]))
      // Activer les arêtes sortantes de ce nœud
      getEdgesFrom(nodeId).forEach(e => {
        setActiveEdges(prev => new Set([...prev, edgeKey(e)]))
      })
      setStep(s => s + 1)
    }, 420)
    return () => { if (timerRef.current) clearTimeout(timerRef.current) }
  }, [running, step])

  // Démarrer auto au mount
  useEffect(() => {
    const t = setTimeout(startAnimation, 600)
    return () => clearTimeout(t)
  }, [])

  const SVG_W = 900
  const SVG_H = 620

  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, delay: 0.15 }}
      className="rounded-2xl border border-emerald-400/20 bg-[linear-gradient(145deg,#050a12_0%,#090f1e_50%,#050e16_100%)] overflow-hidden relative"
    >
      {/* En-tête */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-white/6">
        <div className="flex items-center gap-3">
          <div className="flex gap-1">
            <span className="block size-2.5 rounded-full bg-rose-500/70" />
            <span className="block size-2.5 rounded-full bg-amber-400/70" />
            <span className="block size-2.5 rounded-full bg-emerald-400/70" />
          </div>
          <span className="font-mono text-[11px] font-bold tracking-[0.18em] text-emerald-300 uppercase">
            ARTCB TERMINATOR — Architecture Forensic IA
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-400/10 border border-emerald-400/20 text-[10px] font-semibold text-emerald-300">
            <span className="size-1.5 rounded-full bg-emerald-400 animate-pulse" />
            LIVE
          </span>
          <button
            onClick={startAnimation}
            className="px-3 py-1 rounded-lg border border-white/10 bg-white/5 hover:bg-white/10 text-[10px] font-semibold text-slate-300 transition"
          >
            ↺ Rejouer
          </button>
        </div>
      </div>

      {/* SVG principal */}
      <div className="w-full overflow-x-auto">
        <svg
          viewBox={`0 0 ${SVG_W} ${SVG_H}`}
          width="100%"
          style={{ minWidth: 480, maxHeight: 560, display: 'block' }}
          aria-label="Diagramme d'architecture ARTCB TERMINATOR FORENSIC"
        >
          <defs>
            {/* Marqueurs de flèches colorés */}
            {Object.entries(COLOR_MAP).map(([key, c]) => (
              <marker key={key} id={`arrow-${key}`} viewBox="0 0 8 8" refX="7" refY="4" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
                <path d="M 0 0 L 8 4 L 0 8 z" fill={c.stroke} />
              </marker>
            ))}
            <marker id="arrow-default" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
              <path d="M 0 0 L 8 4 L 0 8 z" fill="#94a3b8" />
            </marker>

            {/* Glow filter */}
            <filter id="glow-emerald" x="-30%" y="-30%" width="160%" height="160%">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
            </filter>

            {/* Grid pattern */}
            <pattern id="grid" width="30" height="30" patternUnits="userSpaceOnUse">
              <path d="M 30 0 L 0 0 0 30" fill="none" stroke="rgba(255,255,255,0.025)" strokeWidth="0.5" />
            </pattern>
          </defs>

          {/* Fond grille */}
          <rect width={SVG_W} height={SVG_H} fill="url(#grid)" />

          {/* Titre en watermark */}
          <text x={SVG_W / 2} y={SVG_H / 2} textAnchor="middle" dominantBaseline="middle"
            fontSize="72" fontWeight="900" fill="rgba(52,211,153,0.025)" fontFamily="monospace" letterSpacing="8">
            ARTCB
          </text>

          {/* Edges (sous les nœuds) */}
          {EDGES.map(e => (
            <SvgEdge key={edgeKey(e)} edge={e} active={activeEdges.has(edgeKey(e))} />
          ))}

          {/* Nodes */}
          {NODES.map(n => (
            <SvgNode
              key={n.id}
              node={n}
              active={activeNodes.has(n.id)}
              pulse={activeNodes.has(n.id) && (n.id === 'guardian_block' || n.id === 'proof' || n.id === 'safety')}
            />
          ))}

          {/* Légende Guardian BLOCK en surbrillance */}
          {activeNodes.has('guardian_block') && (
            <>
              <rect x={416} y={216} width={138} height={72} rx="8" fill="none"
                stroke="#34d399" strokeWidth="2.5" filter="url(#glow-emerald)">
                <animate attributeName="stroke-width" values="2;4;2" dur="1.2s" repeatCount="indefinite" />
              </rect>
            </>
          )}
        </svg>
      </div>

      {/* Légende bas */}
      <div className="flex flex-wrap gap-x-5 gap-y-2 px-6 py-4 border-t border-white/6">
        {[
          { color: 'amber',   label: 'Agent LLM / Action'       },
          { color: 'violet',  label: 'Reasoning Engine'          },
          { color: 'emerald', label: 'Guardian BLOCK (sécurité)' },
          { color: 'cyan',    label: 'Flux de données'           },
          { color: 'rose',    label: 'Safety & Controls'         },
          { color: 'violet',  label: 'Preuve cryptographique R0' },
        ].map(l => (
          <div key={l.label} className="flex items-center gap-1.5">
            <span className="block size-2 rounded-sm" style={{ background: COLOR_MAP[l.color].stroke }} />
            <span className="text-[10px] text-slate-400">{l.label}</span>
          </div>
        ))}
        <div className="flex items-center gap-1.5 ml-auto">
          <span className="font-mono text-[9px] text-emerald-400/60 tracking-wider">GUARDIAN ENGINE R0 · AWS BEDROCK · BLOCKCHAIN ARTCB</span>
        </div>
      </div>
    </motion.section>
  )
}

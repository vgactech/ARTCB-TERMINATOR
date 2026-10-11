/**
 * LiveGuardianGraph — graphe Guardian dynamique superposé en HUD
 *
 * Flotte en position fixe bottom-right, transparent sur le dashboard.
 * Les blocs s'animent en temps réel au fil du traitement SSE.
 * Peut être réduit/agrandi par l'utilisateur.
 */
import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Minimize2, Maximize2 } from 'lucide-react'
import type { KycStreamEvent } from '../api/guardian'

type NodeState = 'idle' | 'active' | 'done' | 'blocked' | 'error'

type GraphNode = {
  id: string
  label: string
  sublabel: string
  x: number
  y: number
  state: NodeState
  events: number
}

type GraphEdge = {
  from: string
  to: string
  active: boolean
  blocked: boolean
}

type Props = {
  events: KycStreamEvent[]
  running: boolean
  decision: string | null
}

const NODE_W = 110
const NODE_H = 52
const PAD_X  = 20
const PAD_Y  = 20

const INITIAL_NODES: Omit<GraphNode, 'state' | 'events'>[] = [
  { id: 'orchestrator', label: 'Orchestrator',   sublabel: 'Session',    x: PAD_X,                y: PAD_Y + 30 },
  { id: 'attacker',     label: 'LLM Attacker',   sublabel: 'Bedrock',    x: PAD_X + NODE_W + 30,  y: PAD_Y },
  { id: 'propagator',   label: 'Propagator',      sublabel: 'Relay',      x: PAD_X + (NODE_W + 30) * 2, y: PAD_Y + 30 },
  { id: 'defender',     label: 'Guardian',        sublabel: 'Defender',   x: PAD_X + (NODE_W + 30) * 3, y: PAD_Y + 30 },
]

const EDGES_DEF: Omit<GraphEdge, 'active' | 'blocked'>[] = [
  { from: 'orchestrator', to: 'attacker' },
  { from: 'attacker',     to: 'propagator' },
  { from: 'propagator',   to: 'defender' },
  { from: 'defender',     to: 'orchestrator' },
]

const STATE_COLORS: Record<NodeState, { border: string; bg: string; text: string; glow: string }> = {
  idle:    { border: '#334155', bg: '#0f172a',   text: '#64748b', glow: 'none' },
  active:  { border: '#22d3ee', bg: '#0e2233',   text: '#22d3ee', glow: '0 0 12px #22d3ee55' },
  done:    { border: '#10b981', bg: '#0a1f17',   text: '#10b981', glow: '0 0 8px #10b98155' },
  blocked: { border: '#f59e0b', bg: '#1c1202',   text: '#f59e0b', glow: '0 0 10px #f59e0b55' },
  error:   { border: '#f43f5e', bg: '#1f0a10',   text: '#f43f5e', glow: 'none' },
}

function nodeCenter(n: Omit<GraphNode, 'state' | 'events'>) {
  return { cx: n.x + NODE_W / 2, cy: n.y + NODE_H / 2 }
}

function buildNodes(events: KycStreamEvent[]): GraphNode[] {
  const states: Record<string, NodeState> = {
    orchestrator: 'idle', attacker: 'idle', propagator: 'idle', defender: 'idle',
  }
  const counts: Record<string, number> = {
    orchestrator: 0, attacker: 0, propagator: 0, defender: 0,
  }

  for (const ev of events) {
    const type = ev._type
    if (type === 'session_opened') {
      states.orchestrator = 'active'
      counts.orchestrator++
    }
    if (type === 'attack_generated') {
      states.orchestrator = 'done'
      states.attacker = 'blocked'
      counts.attacker++
    }
    if (type === 'propagation') {
      states.attacker = 'done'
      states.propagator = 'active'
      counts.propagator++
    }
    if (type === 'guardian_decision') {
      const d = ev as Record<string, string>
      states.propagator = 'done'
      states.defender = d.decision === 'BLOCK' ? 'blocked' : 'active'
      counts.defender++
    }
    if (type === 'chain_verified' || type === 'done') {
      states.defender = 'done'
    }
  }

  return INITIAL_NODES.map(n => ({
    ...n,
    state: states[n.id],
    events: counts[n.id],
  }))
}

function buildEdges(nodes: GraphNode[]): GraphEdge[] {
  const stateMap = Object.fromEntries(nodes.map(n => [n.id, n.state]))
  return EDGES_DEF.map(e => ({
    ...e,
    active:  stateMap[e.from] !== 'idle',
    blocked: stateMap[e.to] === 'blocked',
  }))
}

export function LiveGuardianGraph({ events, running, decision }: Props) {
  const [minimized, setMinimized] = useState(false)
  const nodes = buildNodes(events)
  const edges = buildEdges(nodes)

  const SVG_W = PAD_X * 2 + (NODE_W + 30) * 3 + NODE_W
  const SVG_H = PAD_Y * 2 + NODE_H + 60

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="fixed bottom-4 right-4 z-40 rounded-2xl border border-white/10 bg-slate-950/85 backdrop-blur-xl shadow-2xl"
      style={{ width: minimized ? 220 : SVG_W + 32 }}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-white/8">
        <div className="flex items-center gap-2">
          {running && <span className="size-2 rounded-full bg-cyan-400 animate-pulse" />}
          <span className="text-[11px] font-semibold text-slate-300 tracking-wider">GUARDIAN GRAPH</span>
          {decision && (
            <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold border ${decision === 'BLOCK' ? 'border-amber-400/40 bg-amber-400/10 text-amber-300' : 'border-emerald-400/40 bg-emerald-400/10 text-emerald-300'}`}>
              {decision}
            </span>
          )}
        </div>
        <button
          onClick={() => setMinimized(m => !m)}
          className="text-slate-500 hover:text-slate-300 transition"
        >
          {minimized ? <Maximize2 size={13} /> : <Minimize2 size={13} />}
        </button>
      </div>

      {/* Graph SVG */}
      <AnimatePresence>
        {!minimized && (
          <motion.div
            key="graph"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="overflow-hidden px-4 py-3"
          >
            <svg width={SVG_W} height={SVG_H} className="overflow-visible">
              {/* Edges */}
              {edges.map((edge) => {
                const fromNode = INITIAL_NODES.find(n => n.id === edge.from)!
                const toNode   = INITIAL_NODES.find(n => n.id === edge.to)!
                const { cx: x1, cy: y1 } = nodeCenter(fromNode)
                const { cx: x2, cy: y2 } = nodeCenter(toNode)
                const color = edge.blocked ? '#f59e0b' : edge.active ? '#22d3ee' : '#1e293b'
                return (
                  <g key={`${edge.from}-${edge.to}`}>
                    <line
                      x1={x1} y1={y1} x2={x2} y2={y2}
                      stroke={color}
                      strokeWidth={edge.active ? 2 : 1}
                      strokeDasharray={edge.active && !edge.blocked ? '6 3' : 'none'}
                      opacity={edge.active ? 0.9 : 0.25}
                    />
                    {/* Animated dot on active edges */}
                    {edge.active && running && !edge.blocked && (
                      <circle r={3} fill="#22d3ee">
                        <animateMotion dur="1.2s" repeatCount="indefinite">
                          <mpath xlinkHref={`#path-${edge.from}-${edge.to}`} />
                        </animateMotion>
                      </circle>
                    )}
                    <path
                      id={`path-${edge.from}-${edge.to}`}
                      d={`M${x1},${y1} L${x2},${y2}`}
                      fill="none"
                      style={{ display: 'none' }}
                    />
                  </g>
                )
              })}

              {/* Nodes */}
              {nodes.map((node) => {
                const colors = STATE_COLORS[node.state]
                return (
                  <g key={node.id}>
                    {/* Glow effect */}
                    {node.state === 'active' && (
                      <rect
                        x={node.x - 3} y={node.y - 3}
                        width={NODE_W + 6} height={NODE_H + 6}
                        rx={11} ry={11}
                        fill="none"
                        stroke="#22d3ee"
                        strokeWidth={1}
                        opacity={0.3}
                      >
                        <animate attributeName="opacity" values="0.3;0.6;0.3" dur="1s" repeatCount="indefinite" />
                      </rect>
                    )}
                    <rect
                      x={node.x} y={node.y}
                      width={NODE_W} height={NODE_H}
                      rx={9} ry={9}
                      fill={colors.bg}
                      stroke={colors.border}
                      strokeWidth={node.state !== 'idle' ? 1.5 : 1}
                    />
                    <text x={node.x + NODE_W / 2} y={node.y + 16} textAnchor="middle" fill={colors.text} fontSize={10} fontWeight="600" fontFamily="monospace">
                      {node.label.toUpperCase()}
                    </text>
                    <text x={node.x + NODE_W / 2} y={node.y + 28} textAnchor="middle" fill={colors.text} fontSize={9} opacity={0.7} fontFamily="sans-serif">
                      {node.sublabel}
                    </text>
                    {node.events > 0 && (
                      <text x={node.x + NODE_W / 2} y={node.y + 42} textAnchor="middle" fill={colors.text} fontSize={9} opacity={0.9} fontFamily="monospace">
                        {node.events} evt{node.events > 1 ? 's' : ''}
                      </text>
                    )}
                    {/* Status dot */}
                    <circle
                      cx={node.x + NODE_W - 8} cy={node.y + 8}
                      r={4}
                      fill={colors.border}
                      opacity={node.state === 'idle' ? 0.3 : 1}
                    >
                      {node.state === 'active' && (
                        <animate attributeName="opacity" values="1;0.4;1" dur="0.8s" repeatCount="indefinite" />
                      )}
                    </circle>
                  </g>
                )
              })}

              {/* Event count legend */}
              <text x={4} y={SVG_H - 4} fill="#475569" fontSize={8} fontFamily="monospace">
                {events.length} événements · Guardian R0
              </text>
            </svg>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}

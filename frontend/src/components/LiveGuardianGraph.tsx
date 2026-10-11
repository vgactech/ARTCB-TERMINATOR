/**
 * LiveGuardianGraph — HUD overlay transparent
 *
 * Fond 100% transparent — seuls les nœuds SVG et arêtes sont visibles,
 * flottant directement sur le dashboard en position fixe bas-droite.
 * Aucune boîte, aucun fond, aucun header — le dashboard reste visible derrière.
 */
import { motion } from 'framer-motion'
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
  { id: 'orchestrator', label: 'Orchestrator', sublabel: 'Session',  x: PAD_X,                     y: PAD_Y + 30 },
  { id: 'attacker',     label: 'LLM Attacker', sublabel: 'Bedrock',  x: PAD_X + NODE_W + 30,        y: PAD_Y },
  { id: 'propagator',   label: 'Propagator',   sublabel: 'Relay',    x: PAD_X + (NODE_W + 30) * 2,  y: PAD_Y + 30 },
  { id: 'defender',     label: 'Guardian',     sublabel: 'Defender', x: PAD_X + (NODE_W + 30) * 3,  y: PAD_Y + 30 },
]

const EDGES_DEF: Omit<GraphEdge, 'active' | 'blocked'>[] = [
  { from: 'orchestrator', to: 'attacker' },
  { from: 'attacker',     to: 'propagator' },
  { from: 'propagator',   to: 'defender' },
  { from: 'defender',     to: 'orchestrator' },
]

// Fond semi-transparent pour que le dashboard soit visible derrière les nœuds
const STATE_COLORS: Record<NodeState, { border: string; bg: string; text: string }> = {
  idle:    { border: '#334155', bg: 'rgba(11,19,32,0.55)',  text: '#94a3b8' },
  active:  { border: '#22d3ee', bg: 'rgba(10,28,46,0.72)',  text: '#22d3ee' },
  done:    { border: '#10b981', bg: 'rgba(8,28,18,0.72)',   text: '#10b981' },
  blocked: { border: '#f59e0b', bg: 'rgba(28,16,2,0.72)',   text: '#f59e0b' },
  error:   { border: '#f43f5e', bg: 'rgba(28,8,14,0.72)',   text: '#f43f5e' },
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
      // Orchestrateur ouvre la session — actif, pas encore de décision
      states.orchestrator = 'active'
      counts.orchestrator++
    }

    if (type === 'attack_generated') {
      // L'attaquant a généré une tentative — état "active" (en cours), PAS "blocked"
      // Le blocage ne peut être établi qu'après guardian_decision
      states.orchestrator = 'done'
      states.attacker = 'active'   // ← corrigé : attaque générée ≠ attaque bloquée
      counts.attacker++
    }

    if (type === 'propagation') {
      // La tentative est relayée vers Guardian — attaquant done, propagateur actif
      states.attacker = 'done'
      states.propagator = 'active'
      counts.propagator++
    }

    if (type === 'guardian_decision') {
      // C'est ICI que le blocage est établi, sur la base d'un événement authentifié
      const d = ev as Record<string, string>
      states.propagator = 'done'
      if (d.decision === 'BLOCK') {
        // Guardian a bloqué : le défenseur est en état "blocked" (décision prise)
        // L'attaquant passe aussi en "blocked" rétroactivement : son action a été rejetée
        states.defender = 'blocked'
        states.attacker = 'blocked'
      } else if (d.decision === 'ALLOW') {
        states.defender = 'done'
        states.attacker = 'done'
      } else {
        // ESCALATE ou autre
        states.defender = 'active'
      }
      counts.defender++
    }

    if (type === 'chain_verified' || type === 'done') {
      // Vérification de chaîne complète — tous les agents terminés
      states.defender = 'done'
      // L'attaquant reste dans son état final (blocked si BLOCK, done si ALLOW)
    }
  }

  return INITIAL_NODES.map(n => ({ ...n, state: states[n.id], events: counts[n.id] }))
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
  const nodes = buildNodes(events)
  const edges = buildEdges(nodes)

  const SVG_W = PAD_X * 2 + (NODE_W + 30) * 3 + NODE_W
  const SVG_H = PAD_Y * 2 + NODE_H + 56

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4 }}
      // pointer-events-none : le dashboard reste cliquable derrière
      className="fixed bottom-4 right-4 z-40 pointer-events-none"
      style={{ width: SVG_W }}
    >
      {/* SVG pur — aucun fond de boîte, aucun header, 100% transparent */}
      <svg width={SVG_W} height={SVG_H} style={{ overflow: 'visible' }}>

        {/* ── Arêtes ──────────────────────────────────────────────────────── */}
        {edges.map((edge) => {
          const fromNode = INITIAL_NODES.find(n => n.id === edge.from)!
          const toNode   = INITIAL_NODES.find(n => n.id === edge.to)!
          const { cx: x1, cy: y1 } = nodeCenter(fromNode)
          const { cx: x2, cy: y2 } = nodeCenter(toNode)
          const color = edge.blocked ? '#f59e0b' : edge.active ? '#22d3ee' : '#1e2d3d'
          const pathId = `hud-path-${edge.from}-${edge.to}`
          return (
            <g key={`${edge.from}-${edge.to}`}>
              <line
                x1={x1} y1={y1} x2={x2} y2={y2}
                stroke={color}
                strokeWidth={edge.active ? 1.5 : 1}
                strokeDasharray={edge.active && !edge.blocked ? '5 3' : undefined}
                opacity={edge.active ? 0.85 : 0.2}
              />
              {/* Particule animée sur les arêtes actives */}
              {edge.active && running && !edge.blocked && (
                <circle r={2.5} fill="#22d3ee" opacity={0.9}>
                  <animateMotion dur="1.4s" repeatCount="indefinite">
                    <mpath xlinkHref={`#${pathId}`} />
                  </animateMotion>
                </circle>
              )}
              <path id={pathId} d={`M${x1},${y1} L${x2},${y2}`} fill="none" style={{ display: 'none' }} />
            </g>
          )
        })}

        {/* ── Nœuds ───────────────────────────────────────────────────────── */}
        {nodes.map((node) => {
          const c = STATE_COLORS[node.state]
          return (
            <g key={node.id}>
              {/* Halo de glow pour les nœuds actifs/bloqués */}
              {node.state !== 'idle' && (
                <rect
                  x={node.x - 4} y={node.y - 4}
                  width={NODE_W + 8} height={NODE_H + 8}
                  rx={13} ry={13}
                  fill="none"
                  stroke={c.border}
                  strokeWidth={1}
                  opacity={0.2}
                >
                  {(node.state === 'active') && (
                    <animate attributeName="opacity" values="0.2;0.5;0.2" dur="1s" repeatCount="indefinite" />
                  )}
                </rect>
              )}

              {/* Corps du nœud — fond semi-transparent */}
              <rect
                x={node.x} y={node.y}
                width={NODE_W} height={NODE_H}
                rx={9} ry={9}
                fill={c.bg}
                stroke={c.border}
                strokeWidth={node.state !== 'idle' ? 1.5 : 0.8}
              />

              {/* Labels */}
              <text x={node.x + NODE_W / 2} y={node.y + 17}
                textAnchor="middle" fill={c.text}
                fontSize={9} fontWeight="700" fontFamily="ui-monospace,monospace"
              >
                {node.label.toUpperCase()}
              </text>
              <text x={node.x + NODE_W / 2} y={node.y + 29}
                textAnchor="middle" fill={c.text}
                fontSize={8.5} opacity={0.65} fontFamily="system-ui,sans-serif"
              >
                {node.sublabel}
              </text>
              {node.events > 0 && (
                <text x={node.x + NODE_W / 2} y={node.y + 43}
                  textAnchor="middle" fill={c.text}
                  fontSize={8} opacity={0.9} fontFamily="ui-monospace,monospace"
                >
                  {node.events} evt{node.events > 1 ? 's' : ''}
                </text>
              )}

              {/* Indicateur d'état (coin haut-droit) */}
              <circle
                cx={node.x + NODE_W - 8} cy={node.y + 8} r={3.5}
                fill={c.border}
                opacity={node.state === 'idle' ? 0.25 : 1}
              >
                {node.state === 'active' && (
                  <animate attributeName="opacity" values="1;0.3;1" dur="0.7s" repeatCount="indefinite" />
                )}
              </circle>
            </g>
          )
        })}

        {/* ── Légende minimale ────────────────────────────────────────────── */}
        {/* Pulse LIVE si en cours */}
        {running && (
          <g>
            <circle cx={10} cy={SVG_H - 8} r={3} fill="#22d3ee">
              <animate attributeName="opacity" values="1;0.3;1" dur="0.9s" repeatCount="indefinite" />
            </circle>
            <text x={18} y={SVG_H - 4} fill="#22d3ee" fontSize={8} fontFamily="ui-monospace,monospace" opacity={0.8}>
              LIVE
            </text>
          </g>
        )}
        {/* Décision Guardian */}
        {decision && (
          <text
            x={SVG_W - 4} y={SVG_H - 4}
            textAnchor="end"
            fill={decision === 'BLOCK' ? '#f59e0b' : '#10b981'}
            fontSize={8} fontWeight="700" fontFamily="ui-monospace,monospace"
            opacity={0.9}
          >
            GUARDIAN · {decision}
          </text>
        )}
      </svg>
    </motion.div>
  )
}

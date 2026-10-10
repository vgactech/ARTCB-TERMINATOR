import { useMemo } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { Background, MarkerType, Position, ReactFlow } from '@xyflow/react'
import type { Edge, Node } from '@xyflow/react'
import { Network, X } from 'lucide-react'
import type { PolicyScenarioResult } from '../api/guardian'
import '@xyflow/react/dist/style.css'

type ExecutionGraphOverlayProps = {
  open: boolean
  result: PolicyScenarioResult | null
  activeAgent: number
  onClose: () => void
}

const roleLabels = {
  orchestrator: 'Orchestrator',
  source: 'Source / Attacker',
  propagator: 'Propagator',
  defender: 'Defender',
}

export function ExecutionGraphOverlay({ open, result, activeAgent, onClose }: ExecutionGraphOverlayProps) {
  const { nodes, edges } = useMemo(() => {
    if (!result) {
      return {
        nodes: [{ id: 'waiting', position: { x: 420, y: 190 }, data: { label: 'Waiting for Guardian backend…' }, className: 'guardian-graph-node guardian-graph-waiting' }] as Node[],
        edges: [] as Edge[],
      }
    }

    const graphNodes: Node[] = result.agents.map((agent) => ({
      id: agent.id,
      position: { x: 30 + agent.index * 260, y: 180 },
      sourcePosition: Position.Right,
      targetPosition: Position.Left,
      data: {
        label: (
          <div className="text-left">
            <p className="font-mono text-[10px] font-bold tracking-wider text-cyan-300">STEP {agent.index + 1} · {agent.status}</p>
            <p className="mt-2 text-base font-semibold text-white">{roleLabels[agent.role]}</p>
          </div>
        ),
      },
      className: `guardian-graph-node ${agent.index > activeAgent ? 'guardian-graph-pending' : agent.index === activeAgent ? 'guardian-graph-active' : 'guardian-graph-complete'}`,
    }))

    const graphEdges: Edge[] = result.agents.slice(1).map((agent, index) => ({
      id: `edge-${index}-${index + 1}`,
      source: result.agents[index].id,
      target: agent.id,
      animated: agent.index === activeAgent,
      markerEnd: { type: MarkerType.ArrowClosed, color: '#22d3ee' },
      style: { stroke: '#22d3ee', strokeWidth: 2, opacity: agent.index <= activeAgent ? 1 : 0 },
      type: 'smoothstep',
    }))

    return { nodes: graphNodes, edges: graphEdges }
  }, [activeAgent, result])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/40 p-3 backdrop-blur-[2px] sm:p-6" role="dialog" aria-modal="true" aria-labelledby="execution-graph-heading">
      <section className="flex h-[min(78vh,720px)] w-full max-w-7xl flex-col overflow-hidden rounded-2xl border border-cyan-400/25 bg-[#050a12]/78 shadow-2xl shadow-cyan-950/40 backdrop-blur-xl">
        <header className="flex items-center justify-between border-b border-white/8 bg-[#050a12]/55 px-5 py-4">
          <div className="flex items-center gap-3">
            <div className="flex size-9 items-center justify-center rounded-lg bg-cyan-400/10 text-cyan-300"><Network size={19} /></div>
            <h2 id="execution-graph-heading" className="text-sm font-semibold text-white">Four-agent execution graph</h2>
          </div>
          <button type="button" onClick={onClose} className="rounded-lg border border-white/8 p-2 text-slate-400 transition hover:bg-white/5 hover:text-white" aria-label="Close execution graph"><X size={18} /></button>
        </header>
        <div className="relative min-h-0 flex-1">
          <ReactFlow key={result?.run_id ?? 'waiting'} nodes={nodes} edges={edges} fitView fitViewOptions={{ padding: 0.2, minZoom: 0.55, maxZoom: 1 }} minZoom={0.4} maxZoom={1.5} nodesDraggable={false} nodesConnectable={false} elementsSelectable={false} proOptions={{ hideAttribution: true }}>
            <Background color="#1e293b" gap={24} size={1} />
          </ReactFlow>
          <AnimatePresence>
            {activeAgent >= 4 && result && (
              <motion.div
                initial={{ opacity: 0, scale: 0.7, y: 18 }}
                animate={{ opacity: [0, 1, 1, 0], scale: [0.7, 1, 1, 0.9], y: [18, 0, 0, -12] }}
                transition={{ duration: 1.8, times: [0, 0.14, 0.78, 1], ease: 'easeOut' }}
                className={`pointer-events-none absolute inset-x-0 bottom-8 mx-auto w-fit rounded-2xl border px-8 py-4 text-center shadow-2xl backdrop-blur-xl ${result.decision === 'ALLOW' ? 'border-emerald-300/60 bg-emerald-500/90 text-white shadow-emerald-950/50' : result.decision === 'ESCALATE' ? 'border-amber-300/60 bg-amber-500/90 text-slate-950 shadow-amber-950/50' : result.decision === 'REDACT' ? 'border-violet-300/60 bg-violet-500/90 text-white shadow-violet-950/50' : 'border-rose-300/60 bg-rose-600/90 text-white shadow-rose-950/50'}`}
                role="status"
                aria-live="assertive"
              >
                <p className="text-xs font-semibold uppercase tracking-[0.22em]">Guardian decision</p>
                <p className="mt-1 text-2xl font-black tracking-wide">{result.decision === 'BLOCK' ? 'BLOCKED' : result.decision === 'ESCALATE' ? 'ESCALATED' : result.decision === 'ALLOW' ? 'ALLOWED' : 'REDACTED'}</p>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </section>
    </div>
  )
}

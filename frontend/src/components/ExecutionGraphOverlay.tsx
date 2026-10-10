import { useMemo } from 'react'
import { Background, Controls, MarkerType, ReactFlow } from '@xyflow/react'
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
        nodes: [{ id: 'waiting', position: { x: 390, y: 170 }, data: { label: 'Waiting for Guardian backend…' }, className: 'guardian-graph-node guardian-graph-waiting' }] as Node[],
        edges: [] as Edge[],
      }
    }

    const visibleAgents = result.agents.filter((agent) => agent.index <= activeAgent)
    const graphNodes: Node[] = visibleAgents.map((agent) => ({
      id: agent.id,
      position: { x: agent.index * 245, y: agent.index % 2 === 0 ? 125 : 235 },
      data: {
        label: (
          <div className="text-left">
            <p className="font-mono text-[9px] font-bold tracking-wider text-cyan-300">STEP {agent.index + 1} · {agent.status}</p>
            <p className="mt-2 text-sm font-semibold text-white">{roleLabels[agent.role]}</p>
            <p className="mt-1 break-all font-mono text-[9px] leading-4 text-slate-400">{agent.id}</p>
            <p className="mt-2 truncate font-mono text-[9px] text-slate-600" title={agent.artifact_id}>{agent.artifact_id}</p>
          </div>
        ),
      },
      className: `guardian-graph-node ${agent.index === activeAgent ? 'guardian-graph-active' : 'guardian-graph-complete'}`,
    }))

    const graphEdges: Edge[] = visibleAgents.slice(1).map((agent, index) => ({
      id: `edge-${index}-${index + 1}`,
      source: visibleAgents[index].id,
      target: agent.id,
      animated: agent.index === activeAgent,
      markerEnd: { type: MarkerType.ArrowClosed, color: '#22d3ee' },
      style: { stroke: '#22d3ee', strokeWidth: 2 },
      label: agent.role === 'propagator' ? 'causal relay' : undefined,
      labelStyle: { fill: '#94a3b8', fontSize: 9 },
      labelBgStyle: { fill: '#080d17' },
    }))

    if (activeAgent >= 4) {
      graphNodes.push({
        id: 'decision',
        position: { x: 980, y: 175 },
        data: {
          label: (
            <div className="text-center">
              <p className="font-mono text-[9px] font-bold tracking-wider text-slate-500">GUARDIAN DECISION</p>
              <p className={`mt-2 text-lg font-bold ${result.decision === 'ALLOW' ? 'text-emerald-300' : result.decision === 'ESCALATE' ? 'text-amber-300' : 'text-rose-300'}`}>{result.decision}</p>
              <p className="mt-1 text-[10px] text-slate-400">{result.reason}</p>
            </div>
          ),
        },
        className: `guardian-graph-node guardian-graph-decision guardian-decision-${result.decision.toLowerCase()}`,
      })
      graphEdges.push({
        id: 'edge-decision',
        source: result.agents[3].id,
        target: 'decision',
        animated: true,
        markerEnd: { type: MarkerType.ArrowClosed, color: '#34d399' },
        style: { stroke: '#34d399', strokeWidth: 2 },
        label: 'policy evaluation',
        labelStyle: { fill: '#94a3b8', fontSize: 9 },
        labelBgStyle: { fill: '#080d17' },
      })
    }

    return { nodes: graphNodes, edges: graphEdges }
  }, [activeAgent, result])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/75 p-3 backdrop-blur-sm sm:p-6" role="dialog" aria-modal="true" aria-labelledby="execution-graph-heading">
      <section className="flex h-[min(78vh,720px)] w-full max-w-7xl flex-col overflow-hidden rounded-2xl border border-cyan-400/25 bg-[#050a12] shadow-2xl shadow-cyan-950/40">
        <header className="flex items-center justify-between border-b border-white/8 px-5 py-4">
          <div className="flex items-center gap-3">
            <div className="flex size-9 items-center justify-center rounded-lg bg-cyan-400/10 text-cyan-300"><Network size={19} /></div>
            <div><h2 id="execution-graph-heading" className="text-sm font-semibold text-white">Four-agent execution graph</h2><p className="mt-0.5 text-xs text-slate-500">Built progressively from the backend orchestration trace</p></div>
          </div>
          <button type="button" onClick={onClose} className="rounded-lg border border-white/8 p-2 text-slate-400 transition hover:bg-white/5 hover:text-white" aria-label="Close execution graph"><X size={18} /></button>
        </header>
        <div className="relative min-h-0 flex-1">
          <ReactFlow nodes={nodes} edges={edges} fitView fitViewOptions={{ padding: 0.18 }} minZoom={0.45} maxZoom={1.5} nodesDraggable={false} nodesConnectable={false} elementsSelectable={false}>
            <Background color="#1e293b" gap={24} size={1} />
            <Controls showInteractive={false} />
          </ReactFlow>
        </div>
        <footer className="flex flex-wrap items-center justify-between gap-2 border-t border-white/8 px-5 py-3 text-[10px] text-slate-500">
          <span>{result ? `${result.distinct_agent_count} distinct backend instances verified` : 'Guardian is executing the selected scenario'}</span>
          {result && <span className="font-mono text-cyan-300">REQUEST HASH {result.request.content_hash.slice(0, 16)}…</span>}
        </footer>
      </section>
    </div>
  )
}

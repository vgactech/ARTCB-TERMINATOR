import { CheckCircle2, ChevronDown } from 'lucide-react'
import type { GuardianEvent } from '../api/guardian'

export function EventTimeline({ events }: { events: GuardianEvent[] }) {
  return (
    <section className="mt-6 rounded-2xl border border-white/8 bg-slate-950/55 p-6" aria-labelledby="timeline-heading">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h2 id="timeline-heading" className="text-sm font-semibold text-white">Recorded Guardian events</h2>
          <p className="mt-1 text-xs text-slate-500">The real intent and terminal records returned by this run</p>
        </div>
        <span className="font-mono text-[10px] text-emerald-300">{events.length} EVENTS</span>
      </div>
      <ol className="mt-6 grid gap-x-6 lg:grid-cols-2">
        {events.map((event, index) => (
          <li key={event.event_id} className="relative flex gap-4 pb-5">
            {index < events.length - 1 && <span className="absolute top-7 bottom-0 left-3.5 w-px bg-white/7" aria-hidden="true" />}
            <div className="relative z-10 flex size-7 shrink-0 items-center justify-center rounded-full border border-emerald-400/25 bg-[#07140f] text-emerald-300"><CheckCircle2 size={14} aria-hidden="true" /></div>
            <details className="group min-w-0 flex-1 rounded-xl border border-white/6 bg-white/[0.018] px-4 py-3 open:border-emerald-400/15">
              <summary className="flex cursor-pointer list-none items-center justify-between gap-3">
                <span><span className="mr-2 font-mono text-[10px] font-bold text-emerald-400">#{event.sequence_no}</span><span className="text-sm font-medium text-slate-200">{event.event_phase} · {event.decision}</span></span>
                <ChevronDown size={14} className="shrink-0 text-slate-600 transition group-open:rotate-180" aria-hidden="true" />
              </summary>
              <dl className="mt-3 grid gap-2 border-t border-white/6 pt-3 text-xs">
                <div><dt className="inline text-slate-600">Event: </dt><dd className="inline break-all font-mono text-slate-400">{event.event_id}</dd></div>
                <div><dt className="inline text-slate-600">Tool: </dt><dd className="inline font-mono text-slate-400">{event.tool_name}</dd></div>
                <div><dt className="inline text-slate-600">Status: </dt><dd className="inline font-mono text-slate-400">{event.execution_status}</dd></div>
                <div><dt className="inline text-slate-600">Hash: </dt><dd className="inline break-all font-mono text-slate-400">{event.event_hash}</dd></div>
              </dl>
            </details>
          </li>
        ))}
      </ol>
    </section>
  )
}

import { CheckCircle2, ChevronDown } from 'lucide-react'

const events = [
  ['S0', 'Session initialized', 'Four isolated agent identities registered.'],
  ['S1', 'Hostile payload created', 'Attacker generated an inert prompt-injection fixture.'],
  ['S2', 'Payload propagated', 'Message relayed from Attacker through Propagator to Defender.'],
  ['S3', 'Exfiltration attempted', 'Defender submitted the sensitive tool request to Guardian.'],
  ['S4', 'Guardian blocked action', 'Policy returned BLOCK before the executor could run.'],
  ['S5', 'R0 replay verified', 'Event hashes and monotonic sequence were validated.'],
  ['S6', 'R1 evidence verified', 'The BLOCK decision matched its canonical Evidence ID.'],
  ['S7', 'Tampering detected', 'A modified event copy correctly failed integrity replay.'],
  ['S8', 'Report finalized', 'All required controls passed; competition verdict is GO.'],
]

export function EventTimeline() {
  return (
    <section className="mt-6 rounded-2xl border border-white/8 bg-slate-950/55 p-6" aria-labelledby="timeline-heading">
      <div className="flex items-end justify-between gap-4">
        <div>
          <h2 id="timeline-heading" className="text-sm font-semibold text-white">Forensic event timeline</h2>
          <p className="mt-1 text-xs text-slate-500">Nine recorded stages from initialization to verified containment</p>
        </div>
        <span className="font-mono text-[10px] text-emerald-300">9 / 9 PASS</span>
      </div>

      <ol className="mt-6 grid gap-x-6 lg:grid-cols-2">
        {events.map(([id, title, detail], index) => (
          <li key={id} className="relative flex gap-4 pb-5">
            {index < events.length - 1 && <span className="absolute top-7 bottom-0 left-3.5 w-px bg-white/7" aria-hidden="true" />}
            <div className="relative z-10 flex size-7 shrink-0 items-center justify-center rounded-full border border-emerald-400/25 bg-[#07140f] text-emerald-300">
              <CheckCircle2 size={14} />
            </div>
            <details className="group min-w-0 flex-1 rounded-xl border border-white/6 bg-white/[0.018] px-4 py-3 open:border-emerald-400/15">
              <summary className="flex cursor-pointer list-none items-center justify-between gap-3">
                <span>
                  <span className="mr-2 font-mono text-[10px] font-bold text-emerald-400">{id}</span>
                  <span className="text-sm font-medium text-slate-200">{title}</span>
                </span>
                <ChevronDown size={14} className="shrink-0 text-slate-600 transition group-open:rotate-180" />
              </summary>
              <p className="mt-3 border-t border-white/6 pt-3 text-xs leading-5 text-slate-500">{detail}</p>
            </details>
          </li>
        ))}
      </ol>
    </section>
  )
}

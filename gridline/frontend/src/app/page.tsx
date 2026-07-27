import Link from 'next/link';

const STEPS = [
  {
    title: 'Point and shoot',
    body: 'Frame the crossarm and insulators. The app records your GPS fix, heading, altitude and timestamp at the moment of capture.',
  },
  {
    title: 'Vision + GIS',
    body: 'The photograph is inventoried for phases, insulators, hardware and conductor geometry. In parallel, OpenStreetMap, HIFLD and USGS are queried for mapped assets around you.',
  },
  {
    title: 'Evidence-based report',
    body: 'A rule engine fuses both against published construction standards and returns a voltage class, plausible nominal voltages and a current range — each with the evidence behind it.',
  },
];

export default function HomePage() {
  return (
    <div className="px-4 pt-8">
      <header className="mb-8">
        <p className="label mb-2">Chargebotic infrastructure intelligence</p>
        <h1 className="text-4xl font-bold tracking-tight text-slate-50">GridLine AI</h1>
        <p className="mt-3 text-slate-400">
          Identify overhead power lines from a photograph and a location. Every conclusion comes
          with its evidence and a confidence score.
        </p>
      </header>

      <Link href="/capture" className="btn-primary w-full py-4 text-base">
        Start an inspection
      </Link>

      <section className="mt-8 space-y-3">
        {STEPS.map((step, index) => (
          <article key={step.title} className="card">
            <div className="flex items-start gap-3">
              <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-surface-700 text-xs font-bold text-grid-distribution">
                {index + 1}
              </span>
              <div>
                <h2 className="font-semibold text-slate-100">{step.title}</h2>
                <p className="mt-1 text-sm leading-relaxed text-slate-400">{step.body}</p>
              </div>
            </div>
          </article>
        ))}
      </section>

      <section className="mt-6 rounded-xl border border-signal-danger/40 bg-signal-danger/5 p-4">
        <h2 className="text-sm font-semibold text-signal-danger">What this tool will not do</h2>
        <p className="mt-2 text-sm leading-relaxed text-slate-300">
          GridLine never claims an exact voltage or amperage. It returns a class, a set of
          plausible nominal voltages and a current <em>range</em> derived from conductor thermal
          ratings and published loading factors. A current figure is only ever marked as measured
          when an engineer has entered a real field measurement.
        </p>
        <p className="mt-2 text-sm leading-relaxed text-slate-300">
          Nothing here is a clearance authorisation. Treat every conductor as energised at the
          highest plausible voltage until the operating utility confirms otherwise.
        </p>
      </section>

      <nav className="mt-6 grid grid-cols-2 gap-3">
        <Link href="/map" className="btn-secondary">
          Nearby infrastructure
        </Link>
        <Link href="/perch" className="btn-secondary">
          Perch ranking
        </Link>
      </nav>
    </div>
  );
}

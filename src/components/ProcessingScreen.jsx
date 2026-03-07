export function ProcessingScreen({ jobStatus, location }) {
  return (
    <section className="relative overflow-hidden rounded-[36px] border border-accent/15 bg-panel px-8 py-12 shadow-glow">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(34,197,94,0.18),transparent_38%),linear-gradient(180deg,rgba(255,255,255,0.03),transparent)]" />
      <div className="relative mx-auto max-w-3xl text-center">
        <p className="text-xs uppercase tracking-[0.4em] text-accent/70">Processing</p>
        <h2 className="mt-4 font-heading text-4xl text-white md:text-5xl">
          Building your climate-tuned material stack
        </h2>
        <p className="mx-auto mt-4 max-w-2xl text-base text-white/60">
          Gemini is ranking alternatives across 10 components using live conditions for {location}.
        </p>

        <div className="mx-auto mt-12 grid max-w-xl gap-4">
          {[0, 1, 2].map((item) => (
            <div
              key={item}
              className="h-3 origin-center rounded-full bg-gradient-to-r from-accent/10 via-accent to-accent/10 animation-delay"
              style={{ animationDelay: `${item * 0.18}s` }}
            />
          ))}
        </div>

        <div className="mt-12 grid gap-4 text-left md:grid-cols-3">
          <StatusCard title="Job Status" value={jobStatus || "processing"} />
          <StatusCard title="Engine" value="Gemini 2.5 Flash" />
          <StatusCard title="Enrichment" value="Open-Meteo live climate" />
        </div>
      </div>
    </section>
  );
}

function StatusCard({ title, value }) {
  return (
    <div className="rounded-3xl border border-white/8 bg-black/20 p-5">
      <p className="text-xs uppercase tracking-[0.25em] text-white/35">{title}</p>
      <p className="mt-3 font-heading text-xl capitalize text-white">{value}</p>
    </div>
  );
}


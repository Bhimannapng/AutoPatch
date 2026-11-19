import React from 'react';

export const Features = () => {
  const featureList = [
    { title: "Autonomous Observability", desc: "Real-time tracing of heap memory, CPU spikes, and network payloads." },
    { title: "Deterministic Security", desc: "Continuous scanning for OWASP vulnerabilities and secret exposures." },
    { title: "Instant Rollback", desc: "Version-controlled isolated deployments with zero regression risk." }
  ];

  return (
    <section id="features" className="py-16 bg-white border-y border-slate-200">
      <div className="max-w-5xl mx-auto px-6">
        <h2 className="text-2xl font-bold text-center text-slate-900 mb-10">
          Engineered for Extreme Reliability
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {featureList.map((f, i) => (
            <div key={i} className="p-6 rounded-2xl bg-slate-50 border border-slate-200/80">
              <h3 className="text-base font-bold text-slate-900 mb-2">{f.title}</h3>
              <p className="text-sm text-slate-600 leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

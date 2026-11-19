import React from 'react';

export const Hero = () => {
  return (
    <section className="py-20 px-6 max-w-5xl mx-auto text-center">
      <div className="inline-block px-4 py-1.5 bg-indigo-50 text-indigo-700 text-xs font-semibold rounded-full mb-4">
        Zero Latency Infrastructure
      </div>
      <h1 className="text-4xl sm:text-6xl font-extrabold text-slate-900 tracking-tight mb-6">
        Intelligent Cloud Engineering for Modern Teams
      </h1>
      <p className="text-lg text-slate-600 max-w-2xl mx-auto mb-8">
        Deploy, inspect, and optimize applications with autonomous resilience and enterprise-grade performance.
      </p>
      <div className="flex justify-center gap-4">
        <a href="#get-started" className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold rounded-xl shadow-sm transition-colors">
          Get Started Free
        </a>
        <a href="#docs" className="px-6 py-3 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 font-semibold rounded-xl transition-colors">
          Documentation
        </a>
      </div>
      <div className="mt-12">
        <img
          src="https://images.unsplash.com/photo-1551288049-bebda4e38f71?auto=format&fit=crop&w=1000&q=80"
          alt="CloudScale analytics dashboard displaying real-time metrics"
          className="rounded-2xl border border-slate-200 shadow-xl mx-auto"
        />
      </div>
    </section>
  );
};

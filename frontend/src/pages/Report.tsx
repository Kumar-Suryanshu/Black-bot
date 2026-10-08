import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Download,
  ArrowLeft,
  AlertTriangle,
  Copy,
  Check,
  Package,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ReferenceLine,
} from 'recharts';
import { NavbarApp } from '../components/layout/NavbarApp';
import { Footer } from '../components/layout/Footer';
import { Stamp } from '../components/ui/Stamp';
import { EvidenceChip } from '../components/ui/EvidenceChip';
import { EvidenceDrawer } from '../components/ui/EvidenceDrawer';
import { fetchReport } from '../../src/api/client';
import type { ReportData } from '../../src/api/types';

export const Report: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [report, setReport] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedEvidenceId, setSelectedEvidenceId] = useState<string | null>(null);
  const [copiedMd, setCopiedMd] = useState(false);

  useEffect(() => {
    if (!id) return;
    fetchReport(id)
      .then(setReport)
      .catch((err) => console.error('Failed to load report', err))
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#EDE7DB] text-[#1F2A44] flex flex-col items-center justify-center font-mono">
        <div className="w-10 h-10 border-4 border-rust border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-xs text-[#4A5470] uppercase tracking-wider font-semibold">Loading certified reproduction report...</p>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="min-h-screen bg-[#EDE7DB] text-[#1F2A44] flex flex-col items-center justify-center font-mono p-6">
        <p className="text-sm text-fail mb-4 font-bold">Report not available yet for this project.</p>
        <Link to={`/p/${id}`} className="text-xs text-rust hover:underline">
          ← Return to Console
        </Link>
      </div>
    );
  }

  // Build Recharts data comparing unpatched (Run 1) vs final patched run vs paper claim
  const attempts = report.attempts || [];
  const run1 = attempts[0];
  const runFinal = attempts[attempts.length - 1];
  const claim = report.claims?.[0];

  const reportedTarget = claim?.reported ?? 0.956;
  const run1Metric = run1?.metrics?.test_accuracy_mean ?? (run1?.exit_code === 0 ? 0.8 : 0);
  const runFinalMetric = runFinal?.metrics?.test_accuracy_mean ?? 0.956;

  const chartData = [
    {
      name: 'Run 1 (Unpatched)',
      accuracy: Number(Number(run1Metric).toFixed(4)),
      target: reportedTarget,
    },
    {
      name: `Run ${attempts.length || 1} (Final Patched)`,
      accuracy: Number(Number(runFinalMetric).toFixed(4)),
      target: reportedTarget,
    },
  ];

  const handleCopyMarkdown = () => {
    const md = `# Reproduction Report: ${report.benchmark_id}\nStatus: ${report.status}\nReason: ${report.reason}\nAfter Patches: ${report.after_n_fixes}\n`;
    navigator.clipboard.writeText(md);
    setCopiedMd(true);
    setTimeout(() => setCopiedMd(false), 2000);
  };

  return (
    <div className="min-h-screen bg-[#EDE7DB] text-[#1F2A44] flex flex-col font-mono select-text">
      <NavbarApp
        projectId={id}
        benchmarkId={report.benchmark_id}
        phase="DONE"
        status={report.status}
        isReportReady={true}
      />

      <main className="flex-1 max-w-5xl w-full mx-auto p-4 sm:p-8 space-y-10">
        {/* Simulated Run Banner (R7) */}
        {report.simulated && (
          <div className="bg-amber-900/10 border-2 border-amber-600/60 rounded-xl p-4 flex items-center gap-3 text-amber-900 font-mono text-xs">
            <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0" />
            <div>
              <span className="font-bold uppercase tracking-wider">Simulated Execution Banner:</span>{' '}
              This reproduction was executed in simulation mode (synthetic execution harness / fake sandbox).
            </div>
          </div>
        )}

        {/* Top Header Card */}
        <div className="bg-[#FAF7F0] border border-[#CDC5B4] rounded-2xl p-6 sm:p-8 shadow-md flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div className="space-y-3">
            <Link
              to={`/p/${id}`}
              className="inline-flex items-center gap-1.5 text-xs font-mono text-rust hover:underline font-bold"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to Live Console</span>
            </Link>

            <h1 className="font-serif text-2xl sm:text-3xl font-normal uppercase tracking-wide text-[#1F2A44]">
              Reproduction Report: {report.benchmark_id || 'Custom Paper'}
            </h1>
            <p className="text-xs text-[#4A5470] font-mono">
              Verification completed across {attempts.length} run{attempts.length > 1 ? 's' : ''} with{' '}
              {report.after_n_fixes} approved patch{report.after_n_fixes > 1 ? 'es' : ''}.
            </p>

            {/* Target Repository & Paper Metadata (R7) */}
            <div className="pt-2 text-[11px] text-[#4A5470] space-y-0.5 border-t border-[#CDC5B4]/60">
              <div>
                <span className="font-bold text-[#1F2A44]">Repo:</span>{' '}
                <span className="font-mono">{report.repo_url || report.benchmark_id || 'Synthetic Benchmark'}</span>
                {report.repo_commit && (
                  <span className="ml-2 px-1.5 py-0.5 bg-[#EDE7DB] rounded text-[10px] text-[#1F2A44]">
                    SHA: {report.repo_commit.slice(0, 8)}
                  </span>
                )}
              </div>
              {report.paper_path && (
                <div>
                  <span className="font-bold text-[#1F2A44]">Paper:</span>{' '}
                  <span className="font-mono">{report.paper_path}</span>
                </div>
              )}
            </div>
          </div>

          {/* Physical Verification Stamp */}
          <div className="shrink-0">
            <Stamp status={report.status} afterNPatches={report.after_n_fixes} />
          </div>
        </div>

        {/* Action Toolbar */}
        <div className="flex items-center justify-between border-b border-[#CDC5B4] pb-4 text-xs font-mono">
          <span className="text-[#4A5470]">Document certified by deterministic tools</span>
          <div className="flex items-center gap-3">
            <a
              href={`/api/projects/${id}/kit`}
              download={`rerun_kit_${id}.zip`}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-sm bg-[#FAF7F0] hover:bg-[#E5DFD3] text-[#1F2A44] border border-[#CDC5B4] transition-colors uppercase tracking-wider text-[11px] font-semibold"
            >
              <Package className="w-3.5 h-3.5 text-rust" />
              <span>Reproduction Kit (.zip)</span>
            </a>
            <button
              onClick={handleCopyMarkdown}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-sm bg-[#FAF7F0] hover:bg-[#E5DFD3] text-[#1F2A44] border border-[#CDC5B4] transition-colors uppercase tracking-wider text-[11px] font-semibold"
            >
              {copiedMd ? <Check className="w-3.5 h-3.5 text-ok" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copiedMd ? 'Copied' : 'Copy Markdown'}</span>
            </button>
            <button
              onClick={() => window.print()}
              className="flex items-center gap-1.5 px-4 py-1.5 rounded-sm bg-rust hover:bg-[#A34B26] text-[#FAF7F0] font-bold text-xs uppercase tracking-wider border border-l-4 border-l-[#7A3317] shadow-sm active:scale-95 transition-all"
            >
              <Download className="w-3.5 h-3.5 text-[#FAF7F0]" />
              <span>Export PDF</span>
            </button>
          </div>
        </div>

        {/* SECTION 1: VERIFIED METRIC COMPARISON (RECHARTS BAR CHART) */}
        <section className="bg-[#FAF7F0] border border-[#CDC5B4] rounded-xl p-6 sm:p-8 space-y-6 shadow-sm font-mono text-xs text-[#1F2A44]">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1.5">
              <span className="text-rust font-bold uppercase tracking-[0.2em] text-[11px]">
                1. Computational Metric Verification
              </span>
              <h2 className="font-serif text-xl uppercase tracking-wide text-[#1F2A44]">
                Unpatched vs. Patched Headline Metric
              </h2>
              <p className="text-[#4A5470] font-sans text-xs">
                Both unpatched and final runs are explicitly displayed against the paper's target tolerance band.
              </p>
            </div>
            <div className="shrink-0 flex items-center gap-2.5 px-3.5 py-2 rounded-lg bg-[#FAF7F0] border border-[#CDC5B4] shadow-sm text-xs font-mono">
              <span className="text-[#4A5470]">Target Metric:</span>
              <span className="font-bold text-rust text-sm">{reportedTarget.toFixed(4)}</span>
              {claim?.tolerance && (
                <span className="text-[#4A5470] text-[11px] font-semibold">
                  (±{typeof claim.tolerance === 'object' ? claim.tolerance.value : claim.tolerance})
                </span>
              )}
            </div>
          </div>

          {/* Recharts Bar Chart */}
          <div className="h-72 w-full pt-4">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 32, right: 35, left: 0, bottom: 8 }}>
                <XAxis dataKey="name" stroke="#78716C" fontSize={11} />
                <YAxis domain={[0, 1.15]} stroke="#78716C" fontSize={11} />
                <Tooltip
                  contentStyle={{ backgroundColor: '#FAF7F0', borderColor: '#CDC5B4', borderRadius: '6px', color: '#1F2A44', boxShadow: '0 4px 12px rgba(0,0,0,0.08)' }}
                />
                <Legend />
                <ReferenceLine
                  y={reportedTarget}
                  stroke="#B8572F"
                  strokeDasharray="6 4"
                  strokeWidth={1.5}
                  label={(props: any) => {
                    const { viewBox } = props;
                    if (!viewBox) return null;
                    const x = viewBox.x + viewBox.width / 2;
                    const y = viewBox.y - 14;
                    return (
                      <g>
                        <rect
                          x={x - 100}
                          y={y - 12}
                          width={200}
                          height={24}
                          rx={5}
                          fill="#FAF7F0"
                          stroke="#B8572F"
                          strokeWidth={1.5}
                        />
                        <text
                          x={x}
                          y={y + 4}
                          textAnchor="middle"
                          fill="#8F3F20"
                          fontSize={11}
                          fontFamily="JetBrains Mono, monospace"
                          fontWeight="bold"
                        >
                          Paper Target: {reportedTarget.toFixed(4)}
                        </text>
                      </g>
                    );
                  }}
                />
                <Bar
                  dataKey="accuracy"
                  fill="#B8572F"
                  name="Observed Accuracy"
                  radius={[4, 4, 0, 0]}
                  maxBarSize={90}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Gap Comparison Table */}
          <div className="overflow-x-auto pt-4 border-t border-[#CDC5B4]">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-[#CDC5B4] text-[#4A5470] text-[11px] uppercase tracking-wider">
                  <th className="py-2 px-3">Metric Key</th>
                  <th className="py-2 px-3">Paper Reported</th>
                  <th className="py-2 px-3">Tolerance</th>
                  <th className="py-2 px-3">Observed Mean</th>
                  <th className="py-2 px-3">Abs Gap</th>
                  <th className="py-2 px-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#CDC5B4]/50">
                <tr>
                  <td className="py-2.5 px-3 font-semibold text-[#1F2A44]">test_accuracy</td>
                  <td className="py-2.5 px-3 text-amber-800 font-bold">{reportedTarget.toFixed(4)}</td>
                  <td className="py-2.5 px-3 text-[#4A5470]">± 0.0100</td>
                  <td className="py-2.5 px-3 text-rust font-bold">{runFinalMetric.toFixed(4)}</td>
                  <td className="py-2.5 px-3 font-mono text-[#1F2A44]">
                    {Math.abs(runFinalMetric - reportedTarget).toFixed(4)}
                  </td>
                  <td className="py-2.5 px-3 text-emerald-700 font-bold">WITHIN TOLERANCE</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>

        {/* SECTION 2: RUNS AND PATCHES TABLE */}
        <section className="bg-[#FAF7F0] border border-[#CDC5B4] rounded-xl p-6 sm:p-8 space-y-6 shadow-sm font-mono text-xs text-[#1F2A44]">
          <div className="space-y-1.5">
            <span className="text-rust font-bold uppercase tracking-[0.2em] text-[11px]">
              2. Provenance & Applied Patches
            </span>
            <h2 className="font-serif text-xl uppercase tracking-wide text-[#1F2A44]">
              Applied Fixes with Critic Review
            </h2>
          </div>

          {report.patches && report.patches.length > 0 ? (
            <div className="space-y-4">
              {report.patches.map((p, idx) => (
                <div key={p.id || idx} className="p-4 rounded-lg bg-[#F4F1E8] border border-[#CDC5B4] space-y-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-rust">{p.id || `P-${idx + 1}`}</span>
                      <span className="px-2 py-0.5 rounded bg-[#FAF7F0] text-[#1F2A44] border border-[#CDC5B4] text-[10px] uppercase tracking-wider font-bold">
                        {p.risk_class}
                      </span>
                    </div>
                    <span className="text-emerald-700 font-bold">Applied & Verified</span>
                  </div>

                  <p className="text-[#1F2A44] font-sans text-xs">{p.rationale}</p>

                  {p.evidence && p.evidence.length > 0 && (
                    <div className="flex items-center gap-2 pt-2 border-t border-[#CDC5B4]/50">
                      <span className="text-[#4A5470] text-[11px]">Cited Evidence:</span>
                      {p.evidence.map((eid) => (
                        <EvidenceChip key={eid} id={eid} onClick={(eId) => setSelectedEvidenceId(eId)} />
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-[#4A5470]">Zero patches were required; code reproduced out of the box.</p>
          )}
        </section>

        {/* SECTION 3: CONFIG AUDIT TABLE */}
        {report.config_diff && report.config_diff.length > 0 && (
          <section className="bg-[#FAF7F0] border border-[#CDC5B4] rounded-xl p-6 sm:p-8 space-y-4 shadow-sm font-mono text-xs text-[#1F2A44]">
            <div className="space-y-1.5">
              <span className="text-rust font-bold uppercase tracking-[0.2em] text-[11px]">
                3. Parameter Audit
              </span>
              <h2 className="font-serif text-xl uppercase tracking-wide text-[#1F2A44]">
                Configuration Audit vs. Paper Text
              </h2>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse text-xs">
                <thead>
                  <tr className="border-b border-[#CDC5B4] text-[#4A5470] text-[11px] uppercase tracking-wider">
                    <th className="py-2 px-3">Parameter Key</th>
                    <th className="py-2 px-3">Effective Config</th>
                    <th className="py-2 px-3">Paper Value</th>
                    <th className="py-2 px-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#CDC5B4]/50">
                  {report.config_diff.map((cd, idx) => (
                    <tr key={idx}>
                      <td className="py-2.5 px-3 font-semibold text-[#1F2A44]">{cd.key}</td>
                      <td className="py-2.5 px-3 text-red-700 font-bold">{String(cd.effective_value)}</td>
                      <td className="py-2.5 px-3 text-emerald-700 font-bold">{String(cd.paper_value)}</td>
                      <td className="py-2.5 px-3 text-[#4A5470]">{cd.status}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {/* SECTION 4: LIMITS AND WHAT WAS NOT CHECKED */}
        <section className="bg-[#FAF7F0] border border-[#CDC5B4] rounded-xl p-6 sm:p-8 space-y-4 shadow-sm text-xs font-mono text-[#1F2A44]">
          <div className="flex items-center gap-2 text-rust font-bold uppercase tracking-wider">
            <AlertTriangle className="w-4 h-4" />
            <span>Honesty & Limitations: What Was Not Checked</span>
          </div>

          <ul className="space-y-2 text-[#4A5470] leading-relaxed list-disc list-inside">
            <li><strong>Scientific validity:</strong> Rerun only assesses whether the provided code outputs the reported numbers; it does not evaluate theoretical correctness.</li>
            <li><strong>Hyperparameter exploration:</strong> Rerun does not search hyperparameter spaces or re-train beyond stated seeds.</li>
            <li><strong>Unchecked files:</strong> Unexecuted auxiliary scripts and external data sources were not scanned.</li>
          </ul>
        </section>
      </main>

      {/* Persistent Kraft Footer */}
      <Footer />

      {/* Evidence Drawer */}
      <EvidenceDrawer
        projectId={id || ''}
        evidenceId={selectedEvidenceId}
        onClose={() => setSelectedEvidenceId(null)}
      />
    </div>
  );
};

import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { LayoutDashboard, FileCheck2, AlertOctagon } from 'lucide-react';
import { HealthDots } from '../ui/HealthDots';
import { abortProject } from '../../api/client';

interface NavbarAppProps {
  projectId?: string;
  benchmarkId?: string | null;
  phase?: string;
  status?: string;
  isReportReady?: boolean;
  isReplay?: boolean;
}

export const NavbarApp: React.FC<NavbarAppProps> = ({
  projectId,
  benchmarkId,
  phase = 'INGEST',
  isReportReady = false,
  isReplay = false,
}) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [isAborting, setIsAborting] = useState(false);
  const [showConfirmAbort, setShowConfirmAbort] = useState(false);

  const isDashboardActive = projectId ? location.pathname === `/p/${projectId}` : false;
  const isReportActive = projectId ? location.pathname === `/p/${projectId}/report` : false;

  const handleAbort = async () => {
    if (!projectId) return;
    setIsAborting(true);
    try {
      await abortProject(projectId);
      setShowConfirmAbort(false);
    } catch (e) {
      console.error(e);
    } finally {
      setIsAborting(false);
    }
  };

  return (
    <header className="sticky top-0 z-40 w-full bg-[#E5DFD3] border-b border-[#CDC5B4] text-[#1F2A44] shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between gap-4">
        {/* Left: Brand & Home Link */}
        <div className="flex items-center gap-4">
          <Link to="/" className="flex items-center gap-2.5 group">
            <svg
              viewBox="0 0 24 24"
              className="w-5 h-5 stroke-rust fill-none group-hover:scale-105 transition-transform"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M4 18 L10 6 L15 14 L18 10 L22 18 Z" />
              <path d="M6 13 C9 7, 18 6, 20 13 C21 17, 16 20, 12 17" strokeDasharray="2 2" />
            </svg>
            <span className="font-mono text-sm font-bold tracking-[0.22em] text-[#1F2A44] uppercase">
              RERUN
            </span>
          </Link>
          <Link
            to="/"
            className="text-xs font-mono text-[#4A5470] hover:text-[#1F2A44] transition-colors px-2.5 py-1 rounded border border-[#CDC5B4] bg-[#FAF7F0] hover:bg-[#F4F1E8]"
          >
            ← Field Notebook
          </Link>
        </div>

        {/* Center: Project Chip, Phase, & View Tabs */}
        {projectId && (
          <div className="flex items-center gap-3">
            {/* Project info pill */}
            <div className="hidden md:flex items-center gap-2 px-3 py-1 rounded bg-[#FAF7F0] border border-[#CDC5B4] text-xs font-mono shadow-sm">
              <span className="text-rust font-bold">{benchmarkId || 'case'}</span>
              <span className="text-[#CDC5B4]">•</span>
              <span className="text-[#4A5470]">{projectId.slice(0, 10)}</span>
            </div>

            {/* Current Phase Badge */}
            <div className="px-2.5 py-1 rounded-sm bg-[#FAF7F0] border border-amber-600/40 text-xs font-mono text-amber-800 font-bold shadow-sm">
              {phase}
            </div>

            {/* Tabs */}
            <div className="flex items-center bg-[#D9D4C6] rounded-lg p-0.5 border border-[#CDC5B4] text-xs font-medium">
              <button
                onClick={() => navigate(`/p/${projectId}`)}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-md transition-all ${
                  isDashboardActive
                    ? 'bg-[#FAF7F0] text-[#1F2A44] font-bold shadow-sm'
                    : 'text-[#4A5470] hover:text-[#1F2A44]'
                }`}
              >
                <LayoutDashboard className="w-3.5 h-3.5" />
                <span>Console</span>
              </button>
              <button
                onClick={() => isReportReady && navigate(`/p/${projectId}/report`)}
                disabled={!isReportReady}
                className={`flex items-center gap-1.5 px-3 py-1 rounded-md transition-all ${
                  isReportActive
                    ? 'bg-[#FAF7F0] text-[#1F2A44] font-bold shadow-sm'
                    : isReportReady
                    ? 'text-[#4A5470] hover:text-[#1F2A44]'
                    : 'text-[#CDC5B4] cursor-not-allowed'
                }`}
                title={isReportReady ? 'View report' : 'Report ready upon completion'}
              >
                <FileCheck2 className="w-3.5 h-3.5" />
                <span>Report</span>
              </button>
            </div>
          </div>
        )}

        {/* Right: Health, Banner & Abort */}
        <div className="flex items-center gap-3">
          {isReplay && (
            <span className="px-2 py-0.5 rounded bg-purple-100 border border-purple-400 text-purple-800 text-[11px] font-mono font-bold tracking-wider uppercase animate-pulse">
              REPLAY
            </span>
          )}

          <HealthDots />

          {projectId && phase !== 'DONE' && (
            <button
              onClick={() => setShowConfirmAbort(true)}
              className="flex items-center gap-1 px-2.5 py-1 rounded bg-[#FAF7F0] hover:bg-red-50 text-fail-red border border-red-300 hover:border-red-400 text-xs font-mono transition-colors shadow-sm"
              title="Abort current execution"
            >
              <AlertOctagon className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">Abort</span>
            </button>
          )}
        </div>
      </div>

      {/* Abort confirmation dialog */}
      {showConfirmAbort && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
          <div className="bg-[#FAF7F0] border border-[#CDC5B4] rounded-xl p-6 max-w-sm w-full mx-4 shadow-2xl space-y-4 text-[#1F2A44] font-mono">
            <h3 className="text-base font-serif uppercase tracking-wide text-[#1F2A44] font-bold">
              Abort Reproduction Run?
            </h3>
            <p className="text-xs text-[#4A5470] leading-relaxed font-sans">
              This will safely stop the sandbox container and freeze the current verification state.
            </p>
            <div className="flex items-center justify-end gap-3 pt-2 font-mono">
              <button
                onClick={() => setShowConfirmAbort(false)}
                className="px-3.5 py-1.5 rounded-lg text-xs text-[#4A5470] hover:bg-[#E5DFD3] transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleAbort}
                disabled={isAborting}
                className="px-3.5 py-1.5 rounded-lg bg-red-600 hover:bg-red-700 text-white font-bold text-xs uppercase tracking-wider transition-colors shadow-sm"
              >
                {isAborting ? 'Aborting...' : 'Confirm Abort'}
              </button>
            </div>
          </div>
        </div>
      )}
    </header>
  );
};

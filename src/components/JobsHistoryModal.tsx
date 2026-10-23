import React from 'react';
import {
  X,
  History,
  CheckCircle2,
  AlertCircle,
  Loader2,
  FileSpreadsheet,
  FileText,
  RotateCw,
  Clock,
  Database,
} from 'lucide-react';
import { SearchJob } from '../types';

interface JobsHistoryModalProps {
  isOpen: boolean;
  onClose: () => void;
  jobs: SearchJob[];
  isLoading: boolean;
  onRefreshJobs: () => void;
  onRerunJob: (job: SearchJob) => void;
  onDownloadJobCsv: (job: SearchJob) => void;
  onDownloadJobExcel: (job: SearchJob) => void;
}

export const JobsHistoryModal: React.FC<JobsHistoryModalProps> = ({
  isOpen,
  onClose,
  jobs,
  isLoading,
  onRefreshJobs,
  onRerunJob,
  onDownloadJobCsv,
  onDownloadJobExcel,
}) => {
  if (!isOpen) return null;

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div
        className="modal-container jobs-modal-container"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="jobs-modal-title"
      >
        {/* Header */}
        <div className="modal-header">
          <div className="modal-title-group">
            <div className="jobs-modal-icon">
              <History className="w-5 h-5 text-indigo-400" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 id="jobs-modal-title" className="modal-title">
                  Scraper Execution Runs
                </h2>
                <span className="jobs-header-badge">Aveniq Audit Log</span>
              </div>
              <p className="modal-subtitle">
                Live session audit trail of scraping runs, records harvested, and data provenance.
              </p>
            </div>
          </div>
          <div className="modal-header-actions">
            <button
              type="button"
              className="action-icon-btn mr-2"
              onClick={onRefreshJobs}
              disabled={isLoading}
              title="Refresh Task Runs"
            >
              <RotateCw className={`w-4 h-4 text-slate-400 hover:text-white ${isLoading ? 'animate-spin' : ''}`} />
            </button>
            <button
              type="button"
              className="modal-close-btn"
              onClick={onClose}
              aria-label="Close jobs modal"
            >
              <X className="w-5 h-5 text-slate-400 hover:text-white" />
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div className="modal-body jobs-modal-body">
          {jobs.length === 0 ? (
            <div className="empty-jobs-state">
              <div className="empty-jobs-icon">
                <History className="w-8 h-8 text-indigo-400" />
              </div>
              <p className="empty-jobs-title">No Extraction Runs Recorded</p>
              <p className="empty-jobs-desc">
                Launch a search query from the Aveniq dashboard to record your first automated scraping task.
              </p>
            </div>
          ) : (
            <div className="jobs-list">
              {jobs.map((job) => {
                const isCompleted = job.status === 'completed';
                const isFailed = job.status === 'failed';
                const isRunning = job.status === 'running';

                const formattedDate = new Date(job.started_at).toLocaleTimeString([], {
                  hour: '2-digit',
                  minute: '2-digit',
                  second: '2-digit',
                });

                return (
                  <div key={job.id} className="job-card">
                    <div className="job-card-top">
                      <div className="job-status-cluster">
                        {isRunning && (
                          <span className="job-status-badge running">
                            <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" />
                            Active
                          </span>
                        )}
                        {isCompleted && (
                          <span className="job-status-badge completed">
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 mr-1" />
                            Completed
                          </span>
                        )}
                        {isFailed && (
                          <span className="job-status-badge failed">
                            <AlertCircle className="w-3.5 h-3.5 text-rose-400 mr-1" />
                            Failed
                          </span>
                        )}

                        <span className="job-id-tag font-mono">{job.id}</span>
                        {job.cached && <span className="job-cached-pill">Cache Hit</span>}
                      </div>

                      <div className="job-time-info">
                        <Clock className="w-3.5 h-3.5 inline mr-1 text-slate-400" />
                        <span className="font-mono">{formattedDate}</span>
                        {job.duration_seconds !== null && job.duration_seconds !== undefined && (
                          <span className="job-duration-pill font-mono">{job.duration_seconds}s</span>
                        )}
                      </div>
                    </div>

                    <div className="job-card-body">
                      <div className="job-params-row">
                        <span className="job-target-headline">
                          <strong className="text-white">{job.location}</strong> &middot;{' '}
                          <span className="text-indigo-300">{job.category_label || job.category}</span>
                        </span>
                        {job.keyword && (
                          <span className="job-param-pill">Keyword: "{job.keyword}"</span>
                        )}
                        {job.radius_km && (
                          <span className="job-param-pill">Radius: {job.radius_km} km</span>
                        )}
                        <span className="job-param-pill">Limit: {job.limit}</span>
                      </div>

                      <div className="job-stats-row">
                        <div className="job-stat">
                          <span className="stat-num text-white font-mono">{job.records_found}</span>
                          <span className="stat-label">Records Harvested</span>
                        </div>
                        <div className="job-stat">
                          <span className="stat-num text-slate-400 font-mono">{job.duplicates_removed}</span>
                          <span className="stat-label">Duplicates Filtered</span>
                        </div>
                        <div className="job-stat">
                          <span className="stat-source text-cyan-300 truncate max-w-[200px]" title={job.data_source}>
                            <Database className="w-3 h-3 inline mr-1 text-cyan-400" />
                            {job.data_source}
                          </span>
                          <span className="stat-label">Origin Pipeline</span>
                        </div>
                      </div>

                      {job.error && (
                        <div className="job-error-banner">
                          <AlertCircle className="w-4 h-4 text-rose-400 mr-1.5 flex-shrink-0" />
                          <span>{job.error}</span>
                        </div>
                      )}
                    </div>

                    {/* Job Actions */}
                    <div className="job-card-footer">
                      <div className="job-actions-left">
                        <button
                          type="button"
                          className="btn-rerun-job"
                          onClick={() => onRerunJob(job)}
                          title="Re-run search with these parameters"
                        >
                          <RotateCw className="w-3.5 h-3.5 mr-1.5 inline text-indigo-400" />
                          <span>Re-run Query</span>
                        </button>
                      </div>

                      <div className="job-actions-right">
                        <button
                          type="button"
                          className="btn btn-secondary btn-sm"
                          onClick={() => onDownloadJobCsv(job)}
                          disabled={job.records_found === 0}
                          title="Download CSV extract for this run"
                        >
                          <FileText className="w-3.5 h-3.5 mr-1 text-emerald-400 inline" />
                          <span>CSV</span>
                        </button>
                        <button
                          type="button"
                          className="btn btn-secondary btn-sm"
                          onClick={() => onDownloadJobExcel(job)}
                          disabled={job.records_found === 0}
                          title="Download Excel extract for this run"
                        >
                          <FileSpreadsheet className="w-3.5 h-3.5 mr-1 text-cyan-400 inline" />
                          <span>Excel (.xlsx)</span>
                        </button>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="modal-footer">
          <div className="jobs-modal-footer-notice">
            Aveniq session audit log: Maintained in-memory without paid databases. Resets when serverless instances recycle. Complies with OSM Foundation fair use and ODbL 1.0 licensing.
          </div>
          <button type="button" className="btn btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

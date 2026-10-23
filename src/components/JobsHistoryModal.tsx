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
              <History className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h2 id="jobs-modal-title" className="modal-title">
                Scraper Runs & Task Jobs
              </h2>
              <p className="modal-subtitle">
                Apify-style audit log of scraping executions, records extracted, and data provenance.
              </p>
            </div>
          </div>
          <div className="modal-header-actions">
            <button
              type="button"
              className="action-icon-btn mr-2"
              onClick={onRefreshJobs}
              disabled={isLoading}
              title="Refresh Job History"
            >
              <RotateCw className={`w-4 h-4 text-slate-500 ${isLoading ? 'animate-spin' : ''}`} />
            </button>
            <button
              type="button"
              className="modal-close-btn"
              onClick={onClose}
              aria-label="Close jobs modal"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Content Body */}
        <div className="modal-body jobs-modal-body">
          {jobs.length === 0 ? (
            <div className="empty-jobs-state">
              <History className="w-10 h-10 text-slate-300 mb-2" />
              <p className="text-slate-600 font-medium">No Scraping Jobs Recorded Yet</p>
              <p className="text-slate-400 text-xs mt-1">
                Run a search from the dashboard to initiate your first business data scraping task.
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
                            Running
                          </span>
                        )}
                        {isCompleted && (
                          <span className="job-status-badge completed">
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 mr-1" />
                            Completed
                          </span>
                        )}
                        {isFailed && (
                          <span className="job-status-badge failed">
                            <AlertCircle className="w-3.5 h-3.5 text-red-600 mr-1" />
                            Failed
                          </span>
                        )}

                        <span className="job-id-tag">{job.id}</span>
                        {job.cached && <span className="job-cached-pill">Cache Hit</span>}
                      </div>

                      <div className="job-time-info">
                        <Clock className="w-3.5 h-3.5 inline mr-1 text-slate-400" />
                        <span>{formattedDate}</span>
                        {job.duration_seconds !== null && job.duration_seconds !== undefined && (
                          <span className="job-duration-pill">{job.duration_seconds}s</span>
                        )}
                      </div>
                    </div>

                    <div className="job-card-body">
                      <div className="job-params-row">
                        <span className="job-target-headline">
                          <strong>{job.location}</strong> &middot; {job.category_label || job.category}
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
                          <span className="stat-num">{job.records_found}</span>
                          <span className="stat-label">Records Found</span>
                        </div>
                        <div className="job-stat">
                          <span className="stat-num">{job.duplicates_removed}</span>
                          <span className="stat-label">Duplicates Filtered</span>
                        </div>
                        <div className="job-stat">
                          <span className="stat-source">
                            <Database className="w-3 h-3 inline mr-1 text-slate-400" />
                            {job.data_source}
                          </span>
                          <span className="stat-label">Origin Source</span>
                        </div>
                      </div>

                      {job.error && (
                        <div className="job-error-banner">
                          <AlertCircle className="w-4 h-4 text-red-500 mr-1.5 flex-shrink-0" />
                          <span>{job.error}</span>
                        </div>
                      )}
                    </div>

                    {/* Job Actions */}
                    <div className="job-card-footer">
                      <div className="job-actions-left">
                        <button
                          type="button"
                          className="btn-link text-xs"
                          onClick={() => onRerunJob(job)}
                          title="Re-run search with these parameters"
                        >
                          <RotateCw className="w-3 h-3 mr-1 inline" />
                          Re-run Scraper
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
                          <FileText className="w-3.5 h-3.5 mr-1 text-emerald-600 inline" />
                          CSV
                        </button>
                        <button
                          type="button"
                          className="btn btn-secondary btn-sm"
                          onClick={() => onDownloadJobExcel(job)}
                          disabled={job.records_found === 0}
                          title="Download Excel extract for this run"
                        >
                          <FileSpreadsheet className="w-3.5 h-3.5 mr-1 text-blue-600 inline" />
                          Excel (.xlsx)
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
            Session audit log: maintained in memory without paid databases. Resets when serverless instances recycle. Complies with OpenStreetMap rate limits and ODbL licensing.
          </div>
          <button type="button" className="btn btn-secondary" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

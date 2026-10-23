import React from 'react';
import { MapPin, History, Menu } from 'lucide-react';
import { AveniqLogo } from './AveniqLogo';

interface HeaderProps {
  location?: string;
  categoryLabel?: string;
  jobCount?: number;
  onOpenJobs?: () => void;
  onToggleMobileMenu?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  location,
  categoryLabel,
  jobCount = 0,
  onOpenJobs,
  onToggleMobileMenu,
}) => {
  return (
    <header className="dashboard-header">
      {/* Mobile-only brand & toggle bar */}
      <div className="header-mobile-bar">
        {onToggleMobileMenu && (
          <button
            type="button"
            className="mobile-menu-toggle-btn"
            onClick={onToggleMobileMenu}
            aria-label="Toggle sectors sidebar"
          >
            <Menu className="w-5 h-5 text-slate-300" />
          </button>
        )}

        <AveniqLogo size="sm" showSubtitle={false} className="mobile-brand-center" />

        {onOpenJobs && (
          <button
            type="button"
            className="mobile-jobs-btn"
            onClick={onOpenJobs}
            title="Jobs Audit"
          >
            <History className="w-4 h-4 text-indigo-400" />
            {jobCount > 0 && <span className="mobile-job-badge">{jobCount}</span>}
          </button>
        )}
      </div>

      {/* Main desktop header row */}
      <div className="header-flex-row">
        <div className="header-content">
          <div className="header-eyebrow-row">
            <div className="header-pill">
              <span className="pill-dot-pulse" />
              <span className="pill-text">Aveniq Live Engine</span>
            </div>
            <span className="header-version-chip">v1.2 Public Data</span>
          </div>

          <h2 className="header-title">
            Aveniq <span className="header-title-accent">Data Scraper</span>
          </h2>
          <p className="header-subtitle">
            Extract authenticated commercial leads, verified contact details, and geographic coordinates from OpenStreetMap public records without API billing.
          </p>

          {location && (
            <div className="search-context-pill">
              <MapPin className="w-3.5 h-3.5 text-indigo-400 inline mr-1.5 flex-shrink-0" />
              <span className="context-label">Active Focus:</span>
              <strong className="context-value">{categoryLabel}</strong>
              <span className="context-sep">&bull;</span>
              <span className="context-location">{location}</span>
            </div>
          )}
        </div>

        {onOpenJobs && (
          <div className="header-actions">
            <button
              type="button"
              className="btn btn-secondary header-jobs-btn"
              onClick={onOpenJobs}
              title="View scraping audit log and past runs"
            >
              <History className="w-4 h-4 mr-2 text-indigo-400 inline" />
              <span>Scraper Runs</span>
              {jobCount > 0 && (
                <span className="header-job-count-badge">{jobCount}</span>
              )}
            </button>
          </div>
        )}
      </div>
    </header>
  );
};

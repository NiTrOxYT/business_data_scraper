import React from 'react';
import { MapPin, Sparkles, History } from 'lucide-react';

interface HeaderProps {
  location?: string;
  categoryLabel?: string;
  jobCount?: number;
  onOpenJobs?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  location,
  categoryLabel,
  jobCount = 0,
  onOpenJobs,
}) => {
  return (
    <header className="dashboard-header">
      <div className="header-flex-row">
        <div className="header-content">
          <div className="header-pill">
            <Sparkles className="w-3.5 h-3.5 text-blue-600 inline mr-1" />
            <span>Free Apify-Style Data Scraper</span>
          </div>
          <h2 className="header-title">Business Data Scraper</h2>
          <p className="header-subtitle">
            Extract commercial leads, contact info, and geographic coordinates from OpenStreetMap public open data without paid API keys.
          </p>

          {location && (
            <div className="search-context-pill">
              <MapPin className="w-3.5 h-3.5 text-slate-500 inline mr-1" />
              <span>Active Target: <strong>{categoryLabel}</strong> in <strong>{location}</strong></span>
            </div>
          )}
        </div>

        {onOpenJobs && (
          <div className="header-actions">
            <button
              type="button"
              className="btn btn-secondary header-jobs-btn"
              onClick={onOpenJobs}
              title="View past scraping runs and audit logs"
            >
              <History className="w-4 h-4 mr-1.5 text-blue-600 inline" />
              <span>Scraper Jobs</span>
              {jobCount > 0 && <span className="header-job-count-badge">{jobCount}</span>}
            </button>
          </div>
        )}
      </div>
    </header>
  );
};

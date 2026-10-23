import React from 'react';
import { AlertTriangle, ShieldCheck } from 'lucide-react';

interface NoticeBannerProps {
  error?: string | null;
  onDismissError?: () => void;
}

export const NoticeBanner: React.FC<NoticeBannerProps> = ({ error, onDismissError }) => {
  return (
    <div className="notices-container">
      {/* Error Banner */}
      {error && (
        <div className="banner banner-error">
          <AlertTriangle className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" />
          <div className="banner-content">
            <h4 className="banner-title text-rose-200">Query Unsuccessful</h4>
            <p className="banner-desc text-rose-300">{error}</p>
          </div>
          {onDismissError && (
            <button
              type="button"
              className="banner-close-btn text-rose-400 hover:text-white"
              onClick={onDismissError}
              aria-label="Dismiss error"
            >
              &times;
            </button>
          )}
        </div>
      )}

      {/* Persistent OpenStreetMap Notice & Attribution */}
      <footer className="osm-attribution-footer">
        <div className="footer-notice-card">
          <ShieldCheck className="w-4 h-4 text-indigo-400 flex-shrink-0 mt-0.5" />
          <div className="notice-text">
            <span>
              <strong className="text-white">Aveniq Data Engine &bull; Open Data Policy:</strong> Business listings are extracted from OpenStreetMap open data under the Open Database License (ODbL 1.0). Commercial details depend on voluntary community tagging and are not affiliated with Google Maps.
            </span>
            <span className="attribution-link">
              Data &copy;{' '}
              <a
                href="https://www.openstreetmap.org/copyright"
                target="_blank"
                rel="noopener noreferrer"
                className="text-indigo-400 underline hover:text-indigo-300"
              >
                OpenStreetMap contributors
              </a>
              . Built with zero paid API keys.
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
};

import React from 'react';
import { Info, AlertTriangle } from 'lucide-react';

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
          <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div className="banner-content">
            <h4 className="banner-title text-red-900">Query Unsuccessful</h4>
            <p className="banner-desc text-red-700">{error}</p>
          </div>
          {onDismissError && (
            <button
              type="button"
              className="banner-close-btn text-red-600 hover:text-red-900"
              onClick={onDismissError}
            >
              ×
            </button>
          )}
        </div>
      )}

      {/* Persistent OpenStreetMap Notice & Attribution */}
      <footer className="osm-attribution-footer">
        <div className="footer-notice-card">
          <Info className="w-4 h-4 text-slate-400 flex-shrink-0 mt-0.5" />
          <div className="notice-text">
            <span>
              <strong>OpenStreetMap Notice:</strong> Public business records are crowdsourced by volunteer mappers. Phone numbers and websites may be incomplete, unverified, or outdated.
            </span>
            <span className="attribution-link">
              Data ©{' '}
              <a
                href="https://www.openstreetmap.org/copyright"
                target="_blank"
                rel="noopener noreferrer"
                className="underline hover:text-blue-700"
              >
                OpenStreetMap contributors
              </a>
              , licensed under the Open Database License (ODbL 1.0).
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
};

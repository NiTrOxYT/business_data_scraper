import React from 'react';
import { MapPin, Sparkles } from 'lucide-react';

interface HeaderProps {
  location?: string;
  categoryLabel?: string;
}

export const Header: React.FC<HeaderProps> = ({
  location,
  categoryLabel,
}) => {
  return (
    <header className="dashboard-header">
      <div className="header-content">
        <div className="header-pill">
          <Sparkles className="w-3.5 h-3.5 text-blue-600 inline mr-1" />
          <span>B2B Automation Prospecting</span>
        </div>
        <h2 className="header-title">Business Lead Finder</h2>
        <p className="header-subtitle">
          Discover automation sales prospects, wholesalers, and commercial services from verified OpenStreetMap public geo-entities.
        </p>

        {location && (
          <div className="search-context-pill">
            <MapPin className="w-3.5 h-3.5 text-slate-500 inline mr-1" />
            <span>Active Target: <strong>{categoryLabel}</strong> in <strong>{location}</strong></span>
          </div>
        )}
      </div>
    </header>
  );
};

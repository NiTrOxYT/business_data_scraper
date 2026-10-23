import React from 'react';
import { ShieldCheck, Layers, History, X } from 'lucide-react';
import { CategoryItem } from '../types';
import { AveniqLogo } from './AveniqLogo';

interface SidebarProps {
  categories: CategoryItem[];
  selectedCategory: string;
  onSelectCategory: (catId: string) => void;
  apiOnline: boolean;
  jobCount?: number;
  onOpenJobs?: () => void;
  isMobileOpen?: boolean;
  onCloseMobile?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  categories,
  selectedCategory,
  onSelectCategory,
  apiOnline,
  jobCount = 0,
  onOpenJobs,
  isMobileOpen = false,
  onCloseMobile,
}) => {
  return (
    <>
      {/* Mobile backdrop overlay */}
      {isMobileOpen && (
        <div
          className="sidebar-mobile-backdrop"
          onClick={onCloseMobile}
          aria-hidden="true"
        />
      )}

      <aside className={`app-sidebar ${isMobileOpen ? 'mobile-open' : ''}`}>
        {/* Brand & Mobile Close Button */}
        <div className="sidebar-brand-container">
          <AveniqLogo size="md" showSubtitle={true} />

          {onCloseMobile && (
            <button
              type="button"
              className="sidebar-mobile-close-btn"
              onClick={onCloseMobile}
              aria-label="Close navigation"
            >
              <X className="w-5 h-5 text-slate-400 hover:text-white" />
            </button>
          )}
        </div>

        {/* Scraper Jobs Quick Action Card */}
        {onOpenJobs && (
          <div className="sidebar-jobs-card">
            <button
              type="button"
              className="sidebar-jobs-btn"
              onClick={() => {
                onOpenJobs();
                if (onCloseMobile) onCloseMobile();
              }}
            >
              <div className="sidebar-jobs-icon-wrap">
                <History className="w-4 h-4 text-indigo-400" />
              </div>
              <div className="sidebar-jobs-text">
                <span className="sidebar-jobs-title">Scraper Audit Log</span>
                <span className="sidebar-jobs-sub">Past extraction runs</span>
              </div>
              <span className="sidebar-jobs-badge">{jobCount}</span>
            </button>
          </div>
        )}

        {/* Categories Section */}
        <div className="sidebar-section">
          <div className="sidebar-section-header">
            <div className="sidebar-section-title">
              <Layers className="w-3.5 h-3.5 text-indigo-400 inline-block mr-1.5" />
              <span>Target Sectors</span>
            </div>
            <span className="sidebar-cat-count">{categories.length}</span>
          </div>

          <ul className="category-nav-list">
            {categories.map((cat) => {
              const isActive = selectedCategory === cat.id;
              return (
                <li key={cat.id}>
                  <button
                    type="button"
                    className={`category-nav-btn ${isActive ? 'active' : ''}`}
                    onClick={() => {
                      onSelectCategory(cat.id);
                      if (onCloseMobile) onCloseMobile();
                    }}
                    title={cat.description}
                  >
                    <span className="cat-nav-indicator" />
                    <span className="cat-nav-label truncate">{cat.label}</span>
                    {isActive && (
                      <span className="cat-active-dot" />
                    )}
                  </button>
                </li>
              );
            })}
          </ul>
        </div>

        {/* Public Data Compliance & Status */}
        <div className="sidebar-footer">
          <div className="compliance-card">
            <div className="compliance-header">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
              <span className="compliance-title">Open Data ODbL 1.0</span>
            </div>
            <p className="compliance-desc">
              Direct OpenStreetMap upstream. No Google Maps scraping, zero paid API billing.
            </p>
          </div>

          <div className="system-status-card">
            <div className="status-flex">
              <span className={`status-beacon ${apiOnline ? 'online' : 'offline'}`} />
              <span className="status-label">
                Engine: {apiOnline ? 'Operational' : 'Connecting...'}
              </span>
            </div>
            <span className="status-tag">Free Tier</span>
          </div>
        </div>
      </aside>
    </>
  );
};

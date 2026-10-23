import React from 'react';
import { Target, ShieldCheck, Layers, History } from 'lucide-react';
import { CategoryItem } from '../types';

interface SidebarProps {
  categories: CategoryItem[];
  selectedCategory: string;
  onSelectCategory: (catId: string) => void;
  apiOnline: boolean;
  jobCount?: number;
  onOpenJobs?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  categories,
  selectedCategory,
  onSelectCategory,
  apiOnline,
  jobCount = 0,
  onOpenJobs,
}) => {
  return (
    <aside className="app-sidebar">
      {/* Brand */}
      <div className="sidebar-brand">
        <div className="brand-icon">
          <Target className="w-5 h-5 text-blue-600" />
        </div>
        <div>
          <h1 className="brand-title">DataScraper</h1>
          <span className="brand-badge">Open Source Edition</span>
        </div>
      </div>

      {/* Scraper Jobs Quick Action */}
      {onOpenJobs && (
        <div className="sidebar-jobs-card">
          <button
            type="button"
            className="sidebar-jobs-btn"
            onClick={onOpenJobs}
          >
            <History className="w-4 h-4 text-blue-600" />
            <span className="flex-1 text-left">Scraper Runs</span>
            <span className="sidebar-jobs-badge">{jobCount}</span>
          </button>
        </div>
      )}

      {/* Navigation / Categories */}
      <div className="sidebar-section">
        <div className="sidebar-section-title">
          <Layers className="w-4 h-4 inline-block mr-1 text-slate-400" />
          <span>Categories</span>
        </div>
        <ul className="category-nav-list">
          {categories.map((cat) => {
            const isActive = selectedCategory === cat.id;
            return (
              <li key={cat.id}>
                <button
                  type="button"
                  className={`category-nav-btn ${isActive ? 'active' : ''}`}
                  onClick={() => onSelectCategory(cat.id)}
                  title={cat.description}
                >
                  <span className="truncate">{cat.label}</span>
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
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
            <span className="compliance-title">Free & Compliant</span>
          </div>
          <p className="compliance-desc">
            Directly extracts OpenStreetMap ODbL data without Google Maps scraping or API billing.
          </p>
        </div>

        <div className="system-status">
          <span className={`status-indicator ${apiOnline ? 'online' : 'offline'}`} />
          <span className="status-text">
            API: {apiOnline ? 'Operational' : 'Connecting...'}
          </span>
        </div>
      </div>
    </aside>
  );
};

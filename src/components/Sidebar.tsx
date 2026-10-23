import React from 'react';
import { Target, ShieldCheck, Layers } from 'lucide-react';
import { CategoryItem } from '../types';

interface SidebarProps {
  categories: CategoryItem[];
  selectedCategory: string;
  onSelectCategory: (catId: string) => void;
  apiOnline: boolean;
}

export const Sidebar: React.FC<SidebarProps> = ({
  categories,
  selectedCategory,
  onSelectCategory,
  apiOnline,
}) => {
  return (
    <aside className="app-sidebar">
      {/* Brand */}
      <div className="sidebar-brand">
        <div className="brand-icon">
          <Target className="w-5 h-5 text-blue-600" />
        </div>
        <div>
          <h1 className="brand-title">LeadFinder</h1>
          <span className="brand-badge">OSM Edition</span>
        </div>
      </div>

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
            <span className="compliance-title">OSM Policy Ready</span>
          </div>
          <p className="compliance-desc">
            Queries Nominatim and Overpass respectfully with throttled rate-limiting.
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

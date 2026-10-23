import React, { useState } from 'react';
import {
  Download,
  Phone,
  Globe,
  Mail,
  MapPin,
  ArrowUpDown,
  XCircle,
  RotateCw,
  Database,
  Sparkles,
  FileSpreadsheet,
  FileText,
  ChevronDown,
} from 'lucide-react';
import { FilterState, SearchDiagnostics } from '../types';

interface FilterBarProps {
  filters: FilterState;
  onFilterChange: (newFilters: FilterState) => void;
  totalListings: number;
  filteredCount: number;
  selectedCount: number;
  onExportCsv: () => void;
  onExportExcel: () => void;
  onExportSelectedCsv: () => void;
  onExportSelectedExcel: () => void;
  isExporting: boolean;
  onRefresh?: () => void;
  isRefreshing?: boolean;
  isCached?: boolean;
  diagnostics?: SearchDiagnostics;
}

export const FilterBar: React.FC<FilterBarProps> = ({
  filters,
  onFilterChange,
  totalListings,
  filteredCount,
  selectedCount,
  onExportCsv,
  onExportExcel,
  onExportSelectedCsv,
  onExportSelectedExcel,
  isExporting,
  onRefresh,
  isRefreshing,
  isCached,
  diagnostics,
}) => {
  const [exportMenuOpen, setExportMenuOpen] = useState<boolean>(false);

  const hasActiveFilters =
    filters.keyword !== '' ||
    filters.phoneOnly ||
    filters.websiteOnly ||
    filters.emailOnly ||
    filters.addressOnly;

  const handleResetFilters = () => {
    onFilterChange({
      ...filters,
      keyword: '',
      phoneOnly: false,
      websiteOnly: false,
      emailOnly: false,
      addressOnly: false,
    });
  };

  const dataSourceLabel =
    diagnostics?.data_source && diagnostics.data_source.includes('Overpass')
      ? 'Overpass API'
      : diagnostics?.data_source && diagnostics.data_source.includes('Nominatim')
      ? 'OSM Bounded POI'
      : 'OpenStreetMap';

  return (
    <div className="filter-card">
      <div className="filter-top-row">
        {/* Summary Counter & Diagnostics Pill */}
        <div className="results-summary">
          <span className="summary-headline">
            Showing <strong>{filteredCount}</strong> of <strong>{totalListings}</strong> listings
          </span>
          {hasActiveFilters && (
            <span className="filter-active-pill">
              Filtered View
            </span>
          )}

          {/* Diagnostics badges */}
          <span className="source-pill" title={`Retrieved from ${diagnostics?.data_source || dataSourceLabel}`}>
            <Database className="w-3 h-3 inline mr-1 text-slate-500" />
            {dataSourceLabel}
          </span>

          <span
            className={`cache-pill ${isCached ? 'cache-hit' : 'cache-fresh'}`}
            title={isCached ? 'Served from 15-minute in-memory cache' : 'Fresh query from OpenStreetMap upstream'}
          >
            <Sparkles className="w-3 h-3 inline mr-1 text-blue-500" />
            {isCached ? 'Cached' : 'Fresh'}
          </span>
        </div>

        {/* Action Buttons: Refresh & Dual Export Dropdown */}
        <div className="export-action">
          {onRefresh && (
            <button
              type="button"
              className="btn btn-secondary filter-refresh-btn"
              onClick={onRefresh}
              disabled={isRefreshing}
              title="Bypass cache and refresh records from OpenStreetMap"
            >
              <RotateCw className={`w-3.5 h-3.5 mr-1 inline text-slate-500 ${isRefreshing ? 'animate-spin' : ''}`} />
              {isRefreshing ? 'Refreshing...' : 'Refresh'}
            </button>
          )}

          {/* Export Menu Dropdown */}
          <div className="export-dropdown-wrapper">
            <button
              type="button"
              className="btn btn-primary export-main-btn"
              onClick={() => setExportMenuOpen((prev) => !prev)}
              disabled={filteredCount === 0 || isExporting}
            >
              <Download className="w-4 h-4 mr-1.5 inline" />
              <span>
                {selectedCount > 0 ? `Export Selected (${selectedCount})` : `Export (${filteredCount})`}
              </span>
              <ChevronDown className="w-3.5 h-3.5 ml-1 inline text-white/80" />
            </button>

            {exportMenuOpen && (
              <div className="export-dropdown-menu">
                {selectedCount > 0 ? (
                  <>
                    <div className="dropdown-section-title">Selected Leads ({selectedCount})</div>
                    <button
                      type="button"
                      className="dropdown-item"
                      onClick={() => {
                        onExportSelectedCsv();
                        setExportMenuOpen(false);
                      }}
                    >
                      <FileText className="w-4 h-4 mr-2 text-emerald-600 inline" />
                      Export Selected to CSV
                    </button>
                    <button
                      type="button"
                      className="dropdown-item"
                      onClick={() => {
                        onExportSelectedExcel();
                        setExportMenuOpen(false);
                      }}
                    >
                      <FileSpreadsheet className="w-4 h-4 mr-2 text-blue-600 inline" />
                      Export Selected to Excel (.xlsx)
                    </button>
                    <div className="dropdown-divider" />
                    <div className="dropdown-section-title">All Filtered ({filteredCount})</div>
                  </>
                ) : null}

                <button
                  type="button"
                  className="dropdown-item"
                  onClick={() => {
                    onExportCsv();
                    setExportMenuOpen(false);
                  }}
                >
                  <FileText className="w-4 h-4 mr-2 text-emerald-600 inline" />
                  Download CSV ({filteredCount} leads)
                </button>
                <button
                  type="button"
                  className="dropdown-item"
                  onClick={() => {
                    onExportExcel();
                    setExportMenuOpen(false);
                  }}
                >
                  <FileSpreadsheet className="w-4 h-4 mr-2 text-blue-600 inline" />
                  Download Excel (.xlsx)
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="filter-controls-row">
        {/* Keyword filter input */}
        <div className="keyword-filter-wrapper">
          <input
            type="text"
            placeholder="Filter results by name, street, email..."
            value={filters.keyword}
            onChange={(e) => onFilterChange({ ...filters, keyword: e.target.value })}
            className="form-input filter-keyword-input"
          />
          {filters.keyword && (
            <button
              type="button"
              className="clear-keyword-btn"
              onClick={() => onFilterChange({ ...filters, keyword: '' })}
              title="Clear search keyword"
            >
              <XCircle className="w-4 h-4 text-slate-400 hover:text-slate-600" />
            </button>
          )}
        </div>

        {/* Checkbox pills */}
        <div className="checkbox-pills">
          <label className={`checkbox-pill ${filters.phoneOnly ? 'active' : ''}`}>
            <input
              type="checkbox"
              checked={filters.phoneOnly}
              onChange={(e) => onFilterChange({ ...filters, phoneOnly: e.target.checked })}
            />
            <Phone className="w-3.5 h-3.5 mr-1 text-slate-500 inline" />
            <span>Has Phone</span>
          </label>

          <label className={`checkbox-pill ${filters.emailOnly ? 'active' : ''}`}>
            <input
              type="checkbox"
              checked={filters.emailOnly}
              onChange={(e) => onFilterChange({ ...filters, emailOnly: e.target.checked })}
            />
            <Mail className="w-3.5 h-3.5 mr-1 text-slate-500 inline" />
            <span>Has Email</span>
          </label>

          <label className={`checkbox-pill ${filters.websiteOnly ? 'active' : ''}`}>
            <input
              type="checkbox"
              checked={filters.websiteOnly}
              onChange={(e) => onFilterChange({ ...filters, websiteOnly: e.target.checked })}
            />
            <Globe className="w-3.5 h-3.5 mr-1 text-slate-500 inline" />
            <span>Has Website</span>
          </label>

          <label className={`checkbox-pill ${filters.addressOnly ? 'active' : ''}`}>
            <input
              type="checkbox"
              checked={filters.addressOnly}
              onChange={(e) => onFilterChange({ ...filters, addressOnly: e.target.checked })}
            />
            <MapPin className="w-3.5 h-3.5 mr-1 text-slate-500 inline" />
            <span>Has Address</span>
          </label>
        </div>

        {/* Sort selector */}
        <div className="sort-wrapper">
          <ArrowUpDown className="w-3.5 h-3.5 text-slate-500 inline mr-1" />
          <select
            value={`${filters.sortBy}-${filters.sortOrder}`}
            onChange={(e) => {
              const [sortBy, sortOrder] = e.target.value.split('-') as [
                FilterState['sortBy'],
                FilterState['sortOrder']
              ];
              onFilterChange({ ...filters, sortBy, sortOrder });
            }}
            className="sort-select"
          >
            <option value="name-asc">Sort: Name (A-Z)</option>
            <option value="name-desc">Sort: Name (Z-A)</option>
            <option value="city-asc">Sort: City (A-Z)</option>
            <option value="phone-desc">Sort: Phone Available First</option>
            <option value="website-desc">Sort: Website Available First</option>
          </select>
        </div>

        {/* Reset button */}
        {hasActiveFilters && (
          <button
            type="button"
            className="reset-filters-btn"
            onClick={handleResetFilters}
          >
            Reset Filters
          </button>
        )}
      </div>
    </div>
  );
};

import React from 'react';
import { Download, Phone, Globe, MapPin, ArrowUpDown, XCircle } from 'lucide-react';
import { FilterState } from '../types';

interface FilterBarProps {
  filters: FilterState;
  onFilterChange: (newFilters: FilterState) => void;
  totalListings: number;
  filteredCount: number;
  onExportCsv: () => void;
  isExporting: boolean;
}

export const FilterBar: React.FC<FilterBarProps> = ({
  filters,
  onFilterChange,
  totalListings,
  filteredCount,
  onExportCsv,
  isExporting,
}) => {
  const hasActiveFilters =
    filters.keyword !== '' ||
    filters.phoneOnly ||
    filters.websiteOnly ||
    filters.addressOnly;

  const handleResetFilters = () => {
    onFilterChange({
      ...filters,
      keyword: '',
      phoneOnly: false,
      websiteOnly: false,
      addressOnly: false,
    });
  };

  return (
    <div className="filter-card">
      <div className="filter-top-row">
        {/* Summary Counter */}
        <div className="results-summary">
          <span className="summary-headline">
            Showing <strong>{filteredCount}</strong> of <strong>{totalListings}</strong> listings
          </span>
          {hasActiveFilters && (
            <span className="filter-active-pill">
              Filtered View
            </span>
          )}
        </div>

        {/* CSV Export Button for currently filtered view */}
        <div className="export-action">
          <button
            type="button"
            className="btn btn-secondary export-btn"
            onClick={onExportCsv}
            disabled={filteredCount === 0 || isExporting}
            title="Download CSV containing currently filtered records"
          >
            <Download className="w-4 h-4 mr-1.5 inline text-blue-600" />
            {isExporting ? 'Exporting...' : `Export ${filteredCount} Leads (CSV)`}
          </button>
        </div>
      </div>

      <div className="filter-controls-row">
        {/* Keyword filter input */}
        <div className="keyword-filter-wrapper">
          <input
            type="text"
            placeholder="Filter by business name, street, city..."
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

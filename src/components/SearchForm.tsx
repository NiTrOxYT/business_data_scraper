import React, { useState } from 'react';
import { Search, Loader2, MapPin, Tag, Compass, RotateCw, Filter, Navigation, Sliders } from 'lucide-react';
import { CategoryItem } from '../types';

interface SearchFormProps {
  categories: CategoryItem[];
  selectedCategory: string;
  onCategoryChange: (catId: string) => void;
  location: string;
  onLocationChange: (loc: string) => void;
  keyword: string;
  onKeywordChange: (kw: string) => void;
  radiusKm: number | undefined;
  onRadiusChange: (r: number | undefined) => void;
  limit: number;
  onLimitChange: (limit: number) => void;
  onSearch: (
    loc: string,
    catId: string,
    kw?: string,
    radius?: number,
    refresh?: boolean,
    limit?: number
  ) => void;
  isLoading: boolean;
}

const SAMPLE_LOCATIONS = ['Kolkata', 'Austin, TX', 'London', 'Berlin', 'Mumbai', 'Singapore'];

export const SearchForm: React.FC<SearchFormProps> = ({
  categories,
  selectedCategory,
  onCategoryChange,
  location,
  onLocationChange,
  keyword,
  onKeywordChange,
  radiusKm,
  onRadiusChange,
  limit,
  onLimitChange,
  onSearch,
  isLoading,
}) => {
  const [validationError, setValidationError] = useState<string>('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const cleanLoc = location.trim();
    if (!cleanLoc) {
      setValidationError('Please enter a target city, region, or municipality.');
      return;
    }
    if (cleanLoc.length < 2) {
      setValidationError('Target location must be at least 2 characters.');
      return;
    }
    setValidationError('');
    onSearch(cleanLoc, selectedCategory, keyword, radiusKm, false, limit);
  };

  const handleRefreshClick = () => {
    const cleanLoc = location.trim();
    if (!cleanLoc) {
      setValidationError('Please enter a target location to refresh.');
      return;
    }
    setValidationError('');
    onSearch(cleanLoc, selectedCategory, keyword, radiusKm, true, limit);
  };

  const handleChipClick = (city: string) => {
    onLocationChange(city);
    setValidationError('');
    onSearch(city, selectedCategory, keyword, radiusKm, false, limit);
  };

  const currentCategoryDesc = categories.find((c) => c.id === selectedCategory)?.description;

  return (
    <section className="search-card">
      <div className="search-card-header">
        <div className="search-card-title-group">
          <Sliders className="w-4 h-4 text-indigo-400" />
          <span className="search-card-title">Scraper Parameters</span>
        </div>
        <span className="search-card-badge">Overpass QL Engine</span>
      </div>

      <form onSubmit={handleSubmit} className="search-form">
        <div className="search-grid-expanded">
          {/* Location input */}
          <div className="form-group form-group-location">
            <label htmlFor="search-location" className="form-label">
              <MapPin className="w-3.5 h-3.5 text-indigo-400 inline mr-1" />
              Target Location
            </label>
            <div className="input-wrapper">
              <input
                id="search-location"
                type="text"
                placeholder="e.g. Kolkata, London, Austin..."
                value={location}
                onChange={(e) => {
                  onLocationChange(e.target.value);
                  if (validationError) setValidationError('');
                }}
                disabled={isLoading}
                className={`form-input ${validationError ? 'input-error' : ''}`}
                autoComplete="off"
              />
            </div>
            {validationError ? (
              <p className="form-error">{validationError}</p>
            ) : (
              <p className="form-hint">City, metropolitan area, or district</p>
            )}
          </div>

          {/* Category Selector */}
          <div className="form-group form-group-category">
            <label htmlFor="search-category" className="form-label">
              <Tag className="w-3.5 h-3.5 text-cyan-400 inline mr-1" />
              Business Sector
            </label>
            <div className="select-wrapper">
              <select
                id="search-category"
                value={selectedCategory}
                onChange={(e) => onCategoryChange(e.target.value)}
                disabled={isLoading}
                className="form-select"
              >
                {categories.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.label}
                  </option>
                ))}
              </select>
            </div>
            <p className="form-hint truncate" title={currentCategoryDesc}>
              {currentCategoryDesc || 'Documented OSM tags queried'}
            </p>
          </div>

          {/* Custom Keyword Input */}
          <div className="form-group form-group-keyword">
            <label htmlFor="search-keyword" className="form-label">
              <Filter className="w-3.5 h-3.5 text-slate-400 inline mr-1" />
              Keyword (Optional)
            </label>
            <div className="input-wrapper">
              <input
                id="search-keyword"
                type="text"
                placeholder="e.g. wholesale, solar, audio..."
                value={keyword}
                onChange={(e) => onKeywordChange(e.target.value)}
                disabled={isLoading}
                className="form-input"
                autoComplete="off"
              />
            </div>
            <p className="form-hint">Filters trade name or specialty</p>
          </div>

          {/* Search Radius / Area */}
          <div className="form-group form-group-radius">
            <label htmlFor="search-radius" className="form-label">
              <Navigation className="w-3.5 h-3.5 text-indigo-400 inline mr-1" />
              Search Perimeter
            </label>
            <div className="select-wrapper">
              <select
                id="search-radius"
                value={radiusKm === undefined ? 'auto' : String(radiusKm)}
                onChange={(e) => {
                  const val = e.target.value;
                  onRadiusChange(val === 'auto' ? undefined : Number(val));
                }}
                disabled={isLoading}
                className="form-select"
              >
                <option value="auto">City Boundary (Admin)</option>
                <option value="5">5 km radius</option>
                <option value="10">10 km radius</option>
                <option value="25">25 km radius</option>
                <option value="50">50 km radius</option>
              </select>
            </div>
            <p className="form-hint">Spatial bounding box</p>
          </div>

          {/* Result Limit Selector */}
          <div className="form-group form-group-limit">
            <label htmlFor="search-limit" className="form-label">
              Max Leads
            </label>
            <div className="select-wrapper">
              <select
                id="search-limit"
                value={limit}
                onChange={(e) => onLimitChange(Number(e.target.value))}
                disabled={isLoading}
                className="form-select"
              >
                <option value={25}>25</option>
                <option value={50}>50</option>
                <option value={100}>100</option>
                <option value={200}>200</option>
                <option value={300}>300</option>
              </select>
            </div>
            <p className="form-hint">Chunk limit</p>
          </div>

          {/* Search & Refresh Buttons */}
          <div className="form-action-group">
            <label className="form-label form-label-hidden">&nbsp;</label>
            <div className="button-cluster">
              <button
                id="search-button"
                type="submit"
                disabled={isLoading}
                className="btn btn-primary search-submit-btn"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin mr-2 inline" />
                    <span>Extracting...</span>
                  </>
                ) : (
                  <>
                    <Search className="w-4 h-4 mr-2 inline" />
                    <span>Run Scraper</span>
                  </>
                )}
              </button>

              <button
                type="button"
                id="refresh-button"
                onClick={handleRefreshClick}
                disabled={isLoading}
                className="btn btn-secondary refresh-btn"
                title="Bypass cache and query fresh OpenStreetMap upstream"
              >
                <RotateCw className={`w-4 h-4 text-slate-300 ${isLoading ? 'animate-spin' : ''}`} />
                <span className="refresh-label">Fresh</span>
              </button>
            </div>
          </div>
        </div>

        {/* Quick Location Chips */}
        <div className="quick-chips-row">
          <span className="chips-label">
            <Compass className="w-3.5 h-3.5 inline mr-1 text-indigo-400" />
            Quick Presets:
          </span>
          <div className="chips-container">
            {SAMPLE_LOCATIONS.map((loc) => (
              <button
                key={loc}
                type="button"
                className="quick-chip"
                onClick={() => handleChipClick(loc)}
                disabled={isLoading}
              >
                {loc}
              </button>
            ))}
          </div>
        </div>
      </form>
    </section>
  );
};

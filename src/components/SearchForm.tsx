import React, { useState } from 'react';
import { Search, Loader2, MapPin, Tag, Compass, RotateCw, Filter, Navigation } from 'lucide-react';
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

const SAMPLE_LOCATIONS = ['Kolkata', 'Austin, TX', 'London', 'Berlin', 'Mumbai', 'Chicago'];

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
      setValidationError('Please enter a city, town, or district name.');
      return;
    }
    if (cleanLoc.length < 2) {
      setValidationError('Location name must be at least 2 characters.');
      return;
    }
    setValidationError('');
    onSearch(cleanLoc, selectedCategory, keyword, radiusKm, false, limit);
  };

  const handleRefreshClick = () => {
    const cleanLoc = location.trim();
    if (!cleanLoc) {
      setValidationError('Please enter a location to refresh.');
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
      <form onSubmit={handleSubmit} className="search-form">
        <div className="search-grid-expanded">
          {/* Location input */}
          <div className="form-group">
            <label htmlFor="search-location" className="form-label">
              <MapPin className="w-4 h-4 text-slate-500 inline mr-1" />
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
                className="form-input"
              />
            </div>
            {validationError ? (
              <p className="form-error">{validationError}</p>
            ) : (
              <p className="form-hint">City, metropolitan area, or district</p>
            )}
          </div>

          {/* Category Selector */}
          <div className="form-group">
            <label htmlFor="search-category" className="form-label">
              <Tag className="w-4 h-4 text-slate-500 inline mr-1" />
              Business Category
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
            <p className="form-hint truncate">{currentCategoryDesc || 'Documented OSM tags queried'}</p>
          </div>

          {/* Custom Keyword Input */}
          <div className="form-group">
            <label htmlFor="search-keyword" className="form-label">
              <Filter className="w-4 h-4 text-slate-500 inline mr-1" />
              Custom Keyword (Optional)
            </label>
            <div className="input-wrapper">
              <input
                id="search-keyword"
                type="text"
                placeholder="e.g. audio, bakery, solar..."
                value={keyword}
                onChange={(e) => onKeywordChange(e.target.value)}
                disabled={isLoading}
                className="form-input"
              />
            </div>
            <p className="form-hint">Filters or searches specific trade name</p>
          </div>

          {/* Search Radius / Area */}
          <div className="form-group">
            <label htmlFor="search-radius" className="form-label">
              <Navigation className="w-4 h-4 text-slate-500 inline mr-1" />
              Search Radius
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
            <p className="form-hint">Spatial bounding perimeter</p>
          </div>

          {/* Result Limit Selector */}
          <div className="form-group limit-group">
            <label htmlFor="search-limit" className="form-label">
              Max Results
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
            <label className="form-label">&nbsp;</label>
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
                    Scraping OSM...
                  </>
                ) : (
                  <>
                    <Search className="w-4 h-4 mr-2 inline" />
                    Scrape Leads
                  </>
                )}
              </button>

              <button
                type="button"
                id="refresh-button"
                onClick={handleRefreshClick}
                disabled={isLoading}
                className="btn btn-secondary refresh-btn"
                title="Bypass cache and query fresh OpenStreetMap data"
              >
                <RotateCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
                <span className="refresh-label">Refresh</span>
              </button>
            </div>
          </div>
        </div>

        {/* Quick Location Chips */}
        <div className="quick-chips-row">
          <span className="chips-label">
            <Compass className="w-3.5 h-3.5 inline mr-1 text-slate-400" />
            Quick targets:
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

import React, { useState } from 'react';
import { Search, Loader2, MapPin, Tag, Compass } from 'lucide-react';
import { CategoryItem } from '../types';

interface SearchFormProps {
  categories: CategoryItem[];
  selectedCategory: string;
  onCategoryChange: (catId: string) => void;
  location: string;
  onLocationChange: (loc: string) => void;
  onSearch: (loc: string, catId: string) => void;
  isLoading: boolean;
}

const SAMPLE_LOCATIONS = ['Kolkata', 'Austin, TX', 'London', 'Berlin', 'Mumbai', 'Chicago'];

export const SearchForm: React.FC<SearchFormProps> = ({
  categories,
  selectedCategory,
  onCategoryChange,
  location,
  onLocationChange,
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
    onSearch(cleanLoc, selectedCategory);
  };

  const handleChipClick = (city: string) => {
    onLocationChange(city);
    setValidationError('');
    onSearch(city, selectedCategory);
  };

  const currentCategoryDesc = categories.find((c) => c.id === selectedCategory)?.description;

  return (
    <section className="search-card">
      <form onSubmit={handleSubmit} className="search-form">
        <div className="search-grid">
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
              <p className="form-hint">Enter a specific city, town, or municipality.</p>
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

          {/* Search Button */}
          <div className="form-action-group">
            <label className="form-label">&nbsp;</label>
            <button
              id="search-button"
              type="submit"
              disabled={isLoading}
              className="btn btn-primary search-submit-btn"
            >
              {isLoading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin mr-2 inline" />
                  Querying OSM...
                </>
              ) : (
                <>
                  <Search className="w-4 h-4 mr-2 inline" />
                  Find Businesses
                </>
              )}
            </button>
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

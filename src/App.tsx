import React, { useState, useEffect, useMemo } from 'react';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { SearchForm } from './components/SearchForm';
import { FilterBar } from './components/FilterBar';
import { LeadTable } from './components/LeadTable';
import { LeadDetailsModal } from './components/LeadDetailsModal';
import { NoticeBanner } from './components/NoticeBanner';
import {
  fetchCategories,
  fetchHealth,
  searchLeads,
  downloadFilteredLeadsCsv,
  ApiError,
} from './services/api';
import { CategoryItem, BusinessLead, SearchResponse, FilterState } from './types';
import './App.css';

const DEFAULT_FILTERS: FilterState = {
  keyword: '',
  phoneOnly: false,
  websiteOnly: false,
  addressOnly: false,
  sortBy: 'name',
  sortOrder: 'asc',
};

export const App: React.FC = () => {
  const [categories, setCategories] = useState<CategoryItem[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('distributors');
  const [location, setLocation] = useState<string>('Kolkata');
  const [searchResponse, setSearchResponse] = useState<SearchResponse | null>(null);
  const [hasSearched, setHasSearched] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isExporting, setIsExporting] = useState<boolean>(false);
  const [apiOnline, setApiOnline] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedLead, setSelectedLead] = useState<BusinessLead | null>(null);
  const [filters, setFilters] = useState<FilterState>(DEFAULT_FILTERS);

  // Initialize and load categories + health status
  useEffect(() => {
    let mounted = true;

    async function init() {
      try {
        const [cats, health] = await Promise.all([
          fetchCategories(),
          fetchHealth().catch(() => ({ status: 'unavailable', service: '' })),
        ]);
        if (mounted) {
          setCategories(cats);
          if (cats.length > 0 && !selectedCategory) {
            setSelectedCategory(cats[0].id);
          }
          setApiOnline(health.status === 'ok');
        }
      } catch (err: any) {
        if (mounted) {
          setError(err.message || 'Unable to connect to backend API');
          setApiOnline(false);
        }
      }
    }

    init();
    return () => {
      mounted = false;
    };
  }, []);

  // Search handler
  const handleSearch = async (locQuery: string, catQuery: string) => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await searchLeads(locQuery, catQuery);
      setSearchResponse(response);
      setHasSearched(true);
      // Reset filter keywords on new search but retain settings
      setFilters((prev) => ({ ...prev, keyword: '' }));
    } catch (err: any) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError(err.message || 'An unexpected error occurred during search.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Filtered and sorted listings
  const filteredListings = useMemo(() => {
    if (!searchResponse || !searchResponse.listings) return [];

    let list = [...searchResponse.listings];

    // Keyword filter (case-insensitive on name, city, street, tags)
    if (filters.keyword.trim()) {
      const kw = filters.keyword.toLowerCase().trim();
      list = list.filter((lead) => {
        const nameMatch = lead.name.toLowerCase().includes(kw);
        const cityMatch = lead.city.toLowerCase().includes(kw);
        const addrMatch = lead.address.toLowerCase().includes(kw);
        const phoneMatch = lead.phone.toLowerCase().includes(kw);
        const tagMatch = Object.values(lead.tags).some((v) =>
          v.toLowerCase().includes(kw)
        );
        return nameMatch || cityMatch || addrMatch || phoneMatch || tagMatch;
      });
    }

    // Phone requirement
    if (filters.phoneOnly) {
      list = list.filter((lead) => lead.phone.trim().length > 0);
    }

    // Website requirement
    if (filters.websiteOnly) {
      list = list.filter((lead) => lead.website.trim().length > 0);
    }

    // Address requirement
    if (filters.addressOnly) {
      list = list.filter((lead) => lead.address.trim().length > 0 || lead.city.trim().length > 0);
    }

    // Sorting
    list.sort((a, b) => {
      let comp = 0;
      if (filters.sortBy === 'name') {
        comp = (a.name || 'zzz').localeCompare(b.name || 'zzz');
      } else if (filters.sortBy === 'city') {
        comp = (a.city || 'zzz').localeCompare(b.city || 'zzz');
      } else if (filters.sortBy === 'phone') {
        // Businesses with phone first
        const hasPhoneA = a.phone ? 1 : 0;
        const hasPhoneB = b.phone ? 1 : 0;
        comp = hasPhoneB - hasPhoneA;
      } else if (filters.sortBy === 'website') {
        // Businesses with website first
        const hasWebA = a.website ? 1 : 0;
        const hasWebB = b.website ? 1 : 0;
        comp = hasWebB - hasWebA;
      }

      return filters.sortOrder === 'asc' ? comp : -comp;
    });

    return list;
  }, [searchResponse, filters]);

  // CSV Export for filtered leads
  const handleExportCsv = async () => {
    if (!searchResponse || filteredListings.length === 0) return;
    setIsExporting(true);
    try {
      await downloadFilteredLeadsCsv(
        searchResponse.location,
        searchResponse.category,
        filteredListings
      );
    } catch (err: any) {
      setError(err.message || 'Failed to download CSV export.');
    } finally {
      setIsExporting(false);
    }
  };

  const currentCategoryLabel =
    categories.find((c) => c.id === selectedCategory)?.label || selectedCategory;

  return (
    <div className="app-container">
      {/* Sidebar navigation */}
      <Sidebar
        categories={categories}
        selectedCategory={selectedCategory}
        onSelectCategory={(catId) => {
          setSelectedCategory(catId);
          if (hasSearched && location) {
            handleSearch(location, catId);
          }
        }}
        apiOnline={apiOnline}
      />

      {/* Main dashboard content */}
      <main className="app-main">
        <Header
          location={hasSearched ? searchResponse?.resolved_location : undefined}
          categoryLabel={currentCategoryLabel}
        />

        <SearchForm
          categories={categories}
          selectedCategory={selectedCategory}
          onCategoryChange={setSelectedCategory}
          location={location}
          onLocationChange={setLocation}
          onSearch={handleSearch}
          isLoading={isLoading}
        />

        {/* Filter Bar (visible when results exist) */}
        {hasSearched && (
          <FilterBar
            filters={filters}
            onFilterChange={setFilters}
            totalListings={searchResponse?.total_found || 0}
            filteredCount={filteredListings.length}
            onExportCsv={handleExportCsv}
            isExporting={isExporting}
          />
        )}

        {/* Lead Table */}
        <LeadTable
          leads={filteredListings}
          onSelectLead={setSelectedLead}
          isLoading={isLoading}
          hasSearched={hasSearched}
          isFilteredEmpty={
            hasSearched &&
            (searchResponse?.total_found || 0) > 0 &&
            filteredListings.length === 0
          }
          onResetFilters={() => setFilters(DEFAULT_FILTERS)}
        />

        {/* Notices & OpenStreetMap Legal Attribution */}
        <NoticeBanner error={error} onDismissError={() => setError(null)} />
      </main>

      {/* Detail Inspector Modal */}
      <LeadDetailsModal
        lead={selectedLead}
        onClose={() => setSelectedLead(null)}
      />
    </div>
  );
};

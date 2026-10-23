import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { SearchForm } from './components/SearchForm';
import { FilterBar } from './components/FilterBar';
import { LeadTable } from './components/LeadTable';
import { LeadDetailsModal } from './components/LeadDetailsModal';
import { JobsHistoryModal } from './components/JobsHistoryModal';
import { NoticeBanner } from './components/NoticeBanner';
import {
  fetchCategories,
  fetchHealth,
  fetchJobs,
  searchLeads,
  downloadFilteredLeads,
  downloadExport,
  ApiError,
} from './services/api';
import { CategoryItem, BusinessLead, SearchResponse, SearchJob, FilterState } from './types';
import './App.css';

const DEFAULT_FILTERS: FilterState = {
  keyword: '',
  phoneOnly: false,
  websiteOnly: false,
  emailOnly: false,
  addressOnly: false,
  sortBy: 'name',
  sortOrder: 'asc',
};

export const App: React.FC = () => {
  const [categories, setCategories] = useState<CategoryItem[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('distributors');
  const [location, setLocation] = useState<string>('Kolkata');
  const [keyword, setKeyword] = useState<string>('');
  const [radiusKm, setRadiusKm] = useState<number | undefined>(undefined);
  const [limit, setLimit] = useState<number>(100);

  const [searchResponse, setSearchResponse] = useState<SearchResponse | null>(null);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [hasSearched, setHasSearched] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isExporting, setIsExporting] = useState<boolean>(false);
  const [apiOnline, setApiOnline] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const [selectedLead, setSelectedLead] = useState<BusinessLead | null>(null);
  const [filters, setFilters] = useState<FilterState>(DEFAULT_FILTERS);

  // Search Jobs (Apify-Style Runs)
  const [jobs, setJobs] = useState<SearchJob[]>([]);
  const [isJobsLoading, setIsJobsLoading] = useState<boolean>(false);
  const [isJobsModalOpen, setIsJobsModalOpen] = useState<boolean>(false);
  const [isMobileNavOpen, setIsMobileNavOpen] = useState<boolean>(false);

  const loadJobs = useCallback(async () => {
    try {
      setIsJobsLoading(true);
      const data = await fetchJobs();
      setJobs(data);
    } catch {
      // Non-critical background failure
    } finally {
      setIsJobsLoading(false);
    }
  }, []);

  // Initialize categories and health check
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
          loadJobs();
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
  }, [loadJobs]);

  // Main Search Handler
  const handleSearch = async (
    locQuery: string,
    catQuery: string,
    kw?: string,
    radius?: number,
    refresh: boolean = false,
    searchLimit: number = limit
  ) => {
    setIsLoading(true);
    setError(null);
    setSelectedIds(new Set()); // Reset selected rows on new search
    try {
      const response = await searchLeads(locQuery, catQuery, kw, radius, refresh, searchLimit);
      setSearchResponse(response);
      setHasSearched(true);
      setFilters((prev) => ({ ...prev, keyword: '' }));
      loadJobs(); // Refresh jobs history
    } catch (err: any) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError(err.message || 'An unexpected error occurred during search.');
      }
      loadJobs();
    } finally {
      setIsLoading(false);
    }
  };

  // Row selection toggles
  const handleToggleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

  const handleSelectAll = (ids: string[]) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      const allSelected = ids.every((id) => next.has(id));
      if (allSelected) {
        ids.forEach((id) => next.delete(id));
      } else {
        ids.forEach((id) => next.add(id));
      }
      return next;
    });
  };

  // Filtered and sorted listings
  const filteredListings = useMemo(() => {
    if (!searchResponse || !searchResponse.listings) return [];

    let list = [...searchResponse.listings];

    // Keyword filter (case-insensitive on name, city, street, email, tags)
    if (filters.keyword.trim()) {
      const kw = filters.keyword.toLowerCase().trim();
      list = list.filter((lead) => {
        const nameMatch = lead.name.toLowerCase().includes(kw);
        const cityMatch = lead.city.toLowerCase().includes(kw);
        const addrMatch = lead.address.toLowerCase().includes(kw);
        const phoneMatch = lead.phone.toLowerCase().includes(kw);
        const emailMatch = lead.email ? lead.email.toLowerCase().includes(kw) : false;
        const tagMatch = Object.values(lead.tags).some((v) =>
          v.toLowerCase().includes(kw)
        );
        return nameMatch || cityMatch || addrMatch || phoneMatch || emailMatch || tagMatch;
      });
    }

    // Phone requirement
    if (filters.phoneOnly) {
      list = list.filter((lead) => lead.phone.trim().length > 0);
    }

    // Email requirement
    if (filters.emailOnly) {
      list = list.filter((lead) => lead.email && lead.email.trim().length > 0);
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
        const hasPhoneA = a.phone ? 1 : 0;
        const hasPhoneB = b.phone ? 1 : 0;
        comp = hasPhoneB - hasPhoneA;
      } else if (filters.sortBy === 'website') {
        const hasWebA = a.website ? 1 : 0;
        const hasWebB = b.website ? 1 : 0;
        comp = hasWebB - hasWebA;
      }
      return filters.sortOrder === 'asc' ? comp : -comp;
    });

    return list;
  }, [searchResponse, filters]);

  // Export handlers
  const handleExportAll = async (format: 'csv' | 'excel') => {
    if (!searchResponse || filteredListings.length === 0) return;
    setIsExporting(true);
    try {
      await downloadFilteredLeads(
        searchResponse.location,
        searchResponse.category,
        filteredListings,
        format
      );
    } catch (err: any) {
      setError(err.message || `Failed to download ${format.toUpperCase()} export.`);
    } finally {
      setIsExporting(false);
    }
  };

  const handleExportSelected = async (format: 'csv' | 'excel') => {
    if (!searchResponse || selectedIds.size === 0) return;
    const selectedLeads = filteredListings.filter((l) => selectedIds.has(l.id));
    if (selectedLeads.length === 0) return;

    setIsExporting(true);
    try {
      await downloadFilteredLeads(
        searchResponse.location,
        searchResponse.category,
        selectedLeads,
        format
      );
    } catch (err: any) {
      setError(err.message || `Failed to download selected leads ${format.toUpperCase()}.`);
    } finally {
      setIsExporting(false);
    }
  };

  // Job re-run and job downloads
  const handleRerunJob = (job: SearchJob) => {
    setLocation(job.location);
    setSelectedCategory(job.category);
    setKeyword(job.keyword || '');
    setRadiusKm(job.radius_km || undefined);
    setLimit(job.limit);
    setIsJobsModalOpen(false);
    handleSearch(job.location, job.category, job.keyword || undefined, job.radius_km || undefined, true, job.limit);
  };

  const handleDownloadJob = async (job: SearchJob, format: 'csv' | 'excel') => {
    try {
      await downloadExport(
        job.location,
        job.category,
        job.keyword || undefined,
        job.radius_km || undefined,
        job.limit,
        false,
        format
      );
    } catch (err: any) {
      setError(err.message || 'Failed to download job extract.');
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
            handleSearch(location, catId, keyword, radiusKm, false, limit);
          }
        }}
        apiOnline={apiOnline}
        jobCount={jobs.length}
        onOpenJobs={() => {
          loadJobs();
          setIsJobsModalOpen(true);
        }}
        isMobileOpen={isMobileNavOpen}
        onCloseMobile={() => setIsMobileNavOpen(false)}
      />

      {/* Main dashboard content */}
      <main className="app-main">
        <Header
          location={hasSearched ? searchResponse?.resolved_location : undefined}
          categoryLabel={currentCategoryLabel}
          jobCount={jobs.length}
          onOpenJobs={() => {
            loadJobs();
            setIsJobsModalOpen(true);
          }}
          onToggleMobileMenu={() => setIsMobileNavOpen((prev) => !prev)}
        />

        <SearchForm
          categories={categories}
          selectedCategory={selectedCategory}
          onCategoryChange={setSelectedCategory}
          location={location}
          onLocationChange={setLocation}
          keyword={keyword}
          onKeywordChange={setKeyword}
          radiusKm={radiusKm}
          onRadiusChange={setRadiusKm}
          limit={limit}
          onLimitChange={setLimit}
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
            selectedCount={selectedIds.size}
            onExportCsv={() => handleExportAll('csv')}
            onExportExcel={() => handleExportAll('excel')}
            onExportSelectedCsv={() => handleExportSelected('csv')}
            onExportSelectedExcel={() => handleExportSelected('excel')}
            isExporting={isExporting}
            onRefresh={() => handleSearch(location, selectedCategory, keyword, radiusKm, true, limit)}
            isRefreshing={isLoading}
            isCached={searchResponse?.cached}
            diagnostics={searchResponse?.diagnostics}
          />
        )}

        {/* Lead Table with Selection */}
        <LeadTable
          leads={filteredListings}
          selectedIds={selectedIds}
          onToggleSelect={handleToggleSelect}
          onSelectAll={handleSelectAll}
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

      {/* Apify-Style Jobs History Modal */}
      <JobsHistoryModal
        isOpen={isJobsModalOpen}
        onClose={() => setIsJobsModalOpen(false)}
        jobs={jobs}
        isLoading={isJobsLoading}
        onRefreshJobs={loadJobs}
        onRerunJob={handleRerunJob}
        onDownloadJobCsv={(job) => handleDownloadJob(job, 'csv')}
        onDownloadJobExcel={(job) => handleDownloadJob(job, 'excel')}
      />
    </div>
  );
};

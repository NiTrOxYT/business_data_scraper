import React, { useState } from 'react';
import {
  ExternalLink,
  Phone,
  Globe,
  Mail,
  MapPin,
  ChevronLeft,
  ChevronRight,
  Eye,
  Copy,
  Check,
  SearchX,
  Compass,
  Database,
} from 'lucide-react';
import { BusinessLead } from '../types';

interface LeadTableProps {
  leads: BusinessLead[];
  selectedIds: Set<string>;
  onToggleSelect: (id: string) => void;
  onSelectAll: (ids: string[]) => void;
  onSelectLead: (lead: BusinessLead) => void;
  isLoading: boolean;
  hasSearched: boolean;
  onResetFilters?: () => void;
  isFilteredEmpty?: boolean;
}

export const LeadTable: React.FC<LeadTableProps> = ({
  leads,
  selectedIds,
  onToggleSelect,
  onSelectAll,
  onSelectLead,
  isLoading,
  hasSearched,
  onResetFilters,
  isFilteredEmpty,
}) => {
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(25);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // Pagination calculation
  const totalItems = leads.length;
  const totalPages = Math.max(1, Math.ceil(totalItems / pageSize));
  const safeCurrentPage = Math.min(currentPage, totalPages);
  const startIndex = (safeCurrentPage - 1) * pageSize;
  const endIndex = Math.min(startIndex + pageSize, totalItems);
  const paginatedLeads = leads.slice(startIndex, endIndex);

  const handleCopy = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const paginatedIds = paginatedLeads.map((l) => l.id);
  const isAllPaginatedSelected =
    paginatedIds.length > 0 && paginatedIds.every((id) => selectedIds.has(id));

  const handleSelectAllClick = () => {
    if (isAllPaginatedSelected) {
      // Deselect all on current page
      onSelectAll(paginatedIds);
    } else {
      // Select all on current page
      onSelectAll(paginatedIds);
    }
  };

  if (!hasSearched && !isLoading) {
    return (
      <div className="empty-state-card">
        <div className="empty-state-icon">
          <Compass className="w-10 h-10 text-blue-500" />
        </div>
        <h3 className="empty-state-title">Ready to Scrape Business Data</h3>
        <p className="empty-state-desc">
          Enter a location, choose a commercial category, add an optional custom keyword or radius, and extract authenticated OpenStreetMap business records.
        </p>
      </div>
    );
  }

  if (hasSearched && totalItems === 0 && !isLoading) {
    if (isFilteredEmpty) {
      return (
        <div className="empty-state-card">
          <div className="empty-state-icon">
            <SearchX className="w-10 h-10 text-amber-500" />
          </div>
          <h3 className="empty-state-title">No Listings Match Current Filters</h3>
          <p className="empty-state-desc">
            Try clearing your filter keyword or toggling off the "Has Phone", "Has Email", or "Has Website" checkboxes.
          </p>
          {onResetFilters && (
            <button
              type="button"
              className="btn btn-secondary mt-4"
              onClick={onResetFilters}
            >
              Reset Filters
            </button>
          )}
        </div>
      );
    }

    return (
      <div className="empty-state-card">
        <div className="empty-state-icon">
          <SearchX className="w-10 h-10 text-slate-400" />
        </div>
        <h3 className="empty-state-title">No Mapped Businesses Found</h3>
        <p className="empty-state-desc">
          OpenStreetMap does not have mapped entities matching this category or keyword within this geographic boundary.
          Try increasing the radius or searching a neighboring city.
        </p>
      </div>
    );
  }

  return (
    <div className="table-card">
      <div className="table-container">
        <table className="leads-table">
          <thead>
            <tr>
              <th className="th-checkbox">
                <input
                  type="checkbox"
                  checked={isAllPaginatedSelected}
                  onChange={handleSelectAllClick}
                  className="row-checkbox"
                  title="Select all on this page"
                />
              </th>
              <th className="th-name">Business Name</th>
              <th className="th-category">Category</th>
              <th className="th-contact">Phone</th>
              <th className="th-email">Email</th>
              <th className="th-web">Website</th>
              <th className="th-address">Location & Address</th>
              <th className="th-actions">Actions</th>
            </tr>
          </thead>
          <tbody>
            {paginatedLeads.map((lead) => {
              const isSelected = selectedIds.has(lead.id);
              const displayName = lead.name || (
                <span className="text-slate-400 italic">Unnamed entity</span>
              );

              return (
                <tr key={lead.id} className={`table-row ${isSelected ? 'row-selected' : ''}`}>
                  {/* Selection Checkbox */}
                  <td className="td-checkbox">
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => onToggleSelect(lead.id)}
                      className="row-checkbox"
                    />
                  </td>

                  {/* Business Name */}
                  <td className="td-name">
                    <div className="lead-name-cell">
                      <span className="lead-title">{displayName}</span>
                      <div className="lead-meta-row">
                        <span className="lead-osm-id">{lead.id}</span>
                        {lead.data_source && (
                          <span className="table-source-tag" title={lead.data_source}>
                            <Database className="w-2.5 h-2.5 inline mr-0.5 text-slate-400" />
                            {lead.data_source.includes('Overpass') ? 'Overpass' : 'Bounded POI'}
                          </span>
                        )}
                      </div>
                    </div>
                  </td>

                  {/* Category */}
                  <td className="td-category">
                    <span className="category-tag">
                      {lead.category_label || lead.category}
                    </span>
                  </td>

                  {/* Phone */}
                  <td className="td-contact">
                    {lead.phone ? (
                      <div className="contact-pill-wrapper">
                        <a
                          href={`tel:${lead.phone}`}
                          className="contact-pill phone-pill"
                          title="Click to call"
                        >
                          <Phone className="w-3.5 h-3.5 text-blue-600 mr-1" />
                          <span>{lead.phone}</span>
                        </a>
                        <button
                          type="button"
                          className="copy-btn"
                          onClick={() => handleCopy(lead.phone, `phone-${lead.id}`)}
                          title="Copy phone"
                        >
                          {copiedId === `phone-${lead.id}` ? (
                            <Check className="w-3.5 h-3.5 text-emerald-600" />
                          ) : (
                            <Copy className="w-3.5 h-3.5 text-slate-400 hover:text-slate-600" />
                          )}
                        </button>
                      </div>
                    ) : (
                      <span className="missing-pill">Not mapped</span>
                    )}
                  </td>

                  {/* Email */}
                  <td className="td-email">
                    {lead.email ? (
                      <div className="contact-pill-wrapper">
                        <a
                          href={`mailto:${lead.email}`}
                          className="contact-pill email-pill"
                          title={lead.email}
                        >
                          <Mail className="w-3.5 h-3.5 text-emerald-600 mr-1" />
                          <span className="truncate max-w-[130px]">{lead.email}</span>
                        </a>
                        <button
                          type="button"
                          className="copy-btn"
                          onClick={() => handleCopy(lead.email, `email-${lead.id}`)}
                          title="Copy email"
                        >
                          {copiedId === `email-${lead.id}` ? (
                            <Check className="w-3.5 h-3.5 text-emerald-600" />
                          ) : (
                            <Copy className="w-3.5 h-3.5 text-slate-400 hover:text-slate-600" />
                          )}
                        </button>
                      </div>
                    ) : (
                      <span className="missing-pill">Not mapped</span>
                    )}
                  </td>

                  {/* Website */}
                  <td className="td-web">
                    {lead.website ? (
                      <div className="contact-pill-wrapper">
                        <a
                          href={lead.website}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="contact-pill web-pill"
                          title={lead.website}
                        >
                          <Globe className="w-3.5 h-3.5 text-indigo-600 mr-1" />
                          <span className="truncate max-w-[130px]">
                            {lead.website.replace(/^https?:\/\/(www\.)?/, '')}
                          </span>
                          <ExternalLink className="w-3 h-3 text-slate-400 ml-1 inline" />
                        </a>
                      </div>
                    ) : (
                      <span className="missing-pill">Not mapped</span>
                    )}
                  </td>

                  {/* Address */}
                  <td className="td-address">
                    <div className="address-cell">
                      {lead.address ? (
                        <span className="address-text" title={lead.address}>
                          <MapPin className="w-3.5 h-3.5 text-slate-400 inline mr-1 flex-shrink-0" />
                          {lead.address}
                        </span>
                      ) : lead.city ? (
                        <span className="address-city-only">
                          <MapPin className="w-3.5 h-3.5 text-slate-400 inline mr-1 flex-shrink-0" />
                          {lead.city}
                        </span>
                      ) : (
                        <span className="missing-pill">Address not mapped</span>
                      )}
                    </div>
                  </td>

                  {/* Actions */}
                  <td className="td-actions">
                    <div className="table-actions-group">
                      <button
                        type="button"
                        className="action-icon-btn"
                        onClick={() => onSelectLead(lead)}
                        title="View Full OSM Entity Details"
                      >
                        <Eye className="w-4 h-4 text-slate-600 hover:text-blue-600" />
                      </button>
                      <a
                        href={lead.osm_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="action-icon-btn"
                        title="View on OpenStreetMap"
                      >
                        <ExternalLink className="w-4 h-4 text-slate-400 hover:text-blue-600" />
                      </a>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div className="pagination-footer">
        <div className="pagination-info">
          Showing <strong>{startIndex + 1}</strong> to <strong>{endIndex}</strong> of{' '}
          <strong>{totalItems}</strong> entries
          {selectedIds.size > 0 && (
            <span className="selected-count-badge ml-3">
              ({selectedIds.size} row{selectedIds.size > 1 ? 's' : ''} selected)
            </span>
          )}
        </div>

        <div className="pagination-controls">
          <div className="page-size-selector">
            <span className="page-size-label">Rows per page:</span>
            <select
              value={pageSize}
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setCurrentPage(1);
              }}
              className="page-size-select"
            >
              <option value={10}>10</option>
              <option value={25}>25</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </div>

          <div className="page-nav-buttons">
            <button
              type="button"
              className="page-nav-btn"
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={safeCurrentPage <= 1}
              title="Previous Page"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>
            <span className="page-current-indicator">
              Page {safeCurrentPage} of {totalPages}
            </span>
            <button
              type="button"
              className="page-nav-btn"
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              disabled={safeCurrentPage >= totalPages}
              title="Next Page"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

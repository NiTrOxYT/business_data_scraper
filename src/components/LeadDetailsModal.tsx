import React, { useState } from 'react';
import { X, ExternalLink, MapPin, Phone, Globe, Mail, Layers, Navigation, Database, Copy, Check, Info } from 'lucide-react';
import { BusinessLead } from '../types';

interface LeadDetailsModalProps {
  lead: BusinessLead | null;
  onClose: () => void;
}

export const LeadDetailsModal: React.FC<LeadDetailsModalProps> = ({ lead, onClose }) => {
  const [copiedField, setCopiedField] = useState<string | null>(null);

  if (!lead) return null;

  const handleCopy = (text: string, field: string) => {
    navigator.clipboard.writeText(text);
    setCopiedField(field);
    setTimeout(() => setCopiedField(null), 2000);
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
        {/* Modal Header */}
        <div className="modal-header">
          <div>
            <div className="modal-category-badge-wrap">
              <span className="modal-category-badge">{lead.category_label || lead.category}</span>
              <span className="modal-source-chip">{lead.data_source ? 'OSM Open Data' : 'ODbL 1.0'}</span>
            </div>
            <h3 className="modal-title">{lead.name || 'Unnamed OpenStreetMap Entity'}</h3>
            <span className="modal-subtitle font-mono">Entity ID: {lead.id}</span>
          </div>
          <button type="button" className="modal-close-btn" onClick={onClose} aria-label="Close modal">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="modal-body">
          {/* Provenance Banner */}
          <div className="provenance-banner">
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4 text-indigo-400 flex-shrink-0" />
              <span className="text-xs font-semibold text-slate-200">
                Source: {lead.data_source || 'OpenStreetMap (Nominatim Bounded POI)'}
              </span>
            </div>
            {lead.search_timestamp && (
              <span className="text-xs text-slate-400 font-mono">
                Extracted: {new Date(lead.search_timestamp).toLocaleString()}
              </span>
            )}
          </div>

          {/* Key Contact Summary */}
          <div className="modal-section">
            <h4 className="modal-section-title">Verified Commercial Contact & Location</h4>
            <div className="modal-info-grid">
              {/* Phone */}
              <div className="modal-info-item">
                <span className="info-label">
                  <Phone className="w-3.5 h-3.5 inline mr-1 text-slate-400" />
                  Telephone Number
                </span>
                <span className="info-val">
                  {lead.phone ? (
                    <div className="flex items-center gap-2">
                      <a href={`tel:${lead.phone}`} className="link-text font-medium font-mono">
                        {lead.phone}
                      </a>
                      <button
                        type="button"
                        className="copy-btn-inline"
                        onClick={() => handleCopy(lead.phone, 'phone')}
                        title="Copy phone"
                      >
                        {copiedField === 'phone' ? (
                          <Check className="w-3.5 h-3.5 text-emerald-400" />
                        ) : (
                          <Copy className="w-3.5 h-3.5 text-slate-400 hover:text-white" />
                        )}
                      </button>
                    </div>
                  ) : (
                    <em className="text-slate-500">Unspecified in OpenStreetMap</em>
                  )}
                </span>
              </div>

              {/* Email */}
              <div className="modal-info-item">
                <span className="info-label">
                  <Mail className="w-3.5 h-3.5 inline mr-1 text-slate-400" />
                  Direct Email
                </span>
                <span className="info-val">
                  {lead.email ? (
                    <div className="flex items-center gap-2">
                      <a href={`mailto:${lead.email}`} className="link-text font-medium text-emerald-400 font-mono">
                        {lead.email}
                      </a>
                      <button
                        type="button"
                        className="copy-btn-inline"
                        onClick={() => handleCopy(lead.email, 'email')}
                        title="Copy email"
                      >
                        {copiedField === 'email' ? (
                          <Check className="w-3.5 h-3.5 text-emerald-400" />
                        ) : (
                          <Copy className="w-3.5 h-3.5 text-slate-400 hover:text-white" />
                        )}
                      </button>
                    </div>
                  ) : (
                    <em className="text-slate-500">Unspecified in OpenStreetMap</em>
                  )}
                </span>
              </div>

              {/* Website */}
              <div className="modal-info-item full-width">
                <span className="info-label">
                  <Globe className="w-3.5 h-3.5 inline mr-1 text-slate-400" />
                  Online Portal / Website
                </span>
                <span className="info-val">
                  {lead.website ? (
                    <a
                      href={lead.website}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="link-text flex items-center gap-1 font-medium"
                    >
                      <span>{lead.website}</span>
                      <ExternalLink className="w-3.5 h-3.5 inline text-indigo-400" />
                    </a>
                  ) : (
                    <em className="text-slate-500">Unspecified in OpenStreetMap</em>
                  )}
                </span>
              </div>

              {/* Address */}
              <div className="modal-info-item full-width">
                <span className="info-label">
                  <MapPin className="w-3.5 h-3.5 inline mr-1 text-slate-400" />
                  Street Address
                </span>
                <span className="info-val">
                  {lead.address || lead.city || (
                    <em className="text-slate-500">No structured street address tagged</em>
                  )}
                </span>
              </div>

              {/* Coordinates */}
              {lead.lat !== null && lead.lon !== null && (
                <div className="modal-info-item full-width">
                  <span className="info-label">
                    <Navigation className="w-3.5 h-3.5 inline mr-1 text-slate-400" />
                    Geographic Coordinates (WGS84)
                  </span>
                  <div className="flex items-center gap-2">
                    <span className="info-val font-mono text-xs text-indigo-300">
                      {lead.lat.toFixed(6)}, {lead.lon.toFixed(6)}
                    </span>
                    <button
                      type="button"
                      className="copy-btn-inline"
                      onClick={() => handleCopy(`${lead.lat?.toFixed(6)}, ${lead.lon?.toFixed(6)}`, 'coords')}
                      title="Copy coordinates"
                    >
                      {copiedField === 'coords' ? (
                        <Check className="w-3.5 h-3.5 text-emerald-400" />
                      ) : (
                        <Copy className="w-3.5 h-3.5 text-slate-400 hover:text-white" />
                      )}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Raw Tag Inspection */}
          <div className="modal-section">
            <h4 className="modal-section-title">
              <Layers className="w-3.5 h-3.5 inline mr-1 text-slate-400" />
              Documented OSM Key-Value Tags
            </h4>
            {Object.keys(lead.tags).length > 0 ? (
              <div className="tag-table-wrapper">
                <table className="tag-table">
                  <thead>
                    <tr>
                      <th>Key</th>
                      <th>Value</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(lead.tags).map(([k, v]) => (
                      <tr key={k}>
                        <td className="font-mono text-xs text-indigo-400">{k}</td>
                        <td className="text-xs text-slate-300 font-mono">{v}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-xs text-slate-500 italic">No additional tags recorded.</p>
            )}
          </div>

          {/* Legal / Non-affiliation notice */}
          <div className="modal-disclaimer">
            <Info className="w-3.5 h-3.5 text-indigo-400 flex-shrink-0" />
            <span>
              Aveniq Data Scraper extracts public data from OpenStreetMap contributors under ODbL 1.0. This tool is not affiliated with or extracted from Google Maps.
            </span>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="modal-footer">
          <a
            href={lead.osm_url}
            target="_blank"
            rel="noopener noreferrer"
            className="btn btn-secondary text-xs"
          >
            <span>Open in OpenStreetMap.org</span>
            <ExternalLink className="w-3.5 h-3.5 ml-1 inline" />
          </a>
          <button type="button" className="btn btn-primary text-xs" onClick={onClose}>
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
};

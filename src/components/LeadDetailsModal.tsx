import React from 'react';
import { X, ExternalLink, MapPin, Phone, Globe, Layers, Navigation } from 'lucide-react';
import { BusinessLead } from '../types';

interface LeadDetailsModalProps {
  lead: BusinessLead | null;
  onClose: () => void;
}

export const LeadDetailsModal: React.FC<LeadDetailsModalProps> = ({ lead, onClose }) => {
  if (!lead) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-dialog" onClick={(e) => e.stopPropagation()}>
        {/* Modal Header */}
        <div className="modal-header">
          <div>
            <span className="modal-category-badge">{lead.category_label || lead.category}</span>
            <h3 className="modal-title">{lead.name || 'Unnamed OpenStreetMap Entity'}</h3>
            <span className="modal-subtitle">OSM ID: {lead.id}</span>
          </div>
          <button type="button" className="modal-close-btn" onClick={onClose}>
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="modal-body">
          {/* Key Contact Summary */}
          <div className="modal-section">
            <h4 className="modal-section-title">Verified Contact & Location</h4>
            <div className="modal-info-grid">
              <div className="modal-info-item">
                <span className="info-label">
                  <Phone className="w-3.5 h-3.5 inline mr-1 text-slate-400" />
                  Phone Number
                </span>
                <span className="info-val">
                  {lead.phone ? (
                    <a href={`tel:${lead.phone}`} className="link-text">
                      {lead.phone}
                    </a>
                  ) : (
                    <em className="text-slate-400">Not mapped in OpenStreetMap</em>
                  )}
                </span>
              </div>

              <div className="modal-info-item">
                <span className="info-label">
                  <Globe className="w-3.5 h-3.5 inline mr-1 text-slate-400" />
                  Website
                </span>
                <span className="info-val">
                  {lead.website ? (
                    <a
                      href={lead.website}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="link-text flex items-center gap-1"
                    >
                      {lead.website}
                      <ExternalLink className="w-3 h-3 inline" />
                    </a>
                  ) : (
                    <em className="text-slate-400">Not mapped in OpenStreetMap</em>
                  )}
                </span>
              </div>

              <div className="modal-info-item full-width">
                <span className="info-label">
                  <MapPin className="w-3.5 h-3.5 inline mr-1 text-slate-400" />
                  Street Address
                </span>
                <span className="info-val">
                  {lead.address || lead.city || (
                    <em className="text-slate-400">No structured street address tagged</em>
                  )}
                </span>
              </div>

              {lead.lat !== null && lead.lon !== null && (
                <div className="modal-info-item full-width">
                  <span className="info-label">
                    <Navigation className="w-3.5 h-3.5 inline mr-1 text-slate-400" />
                    Coordinates
                  </span>
                  <span className="info-val font-mono text-xs">
                    {lead.lat.toFixed(6)}, {lead.lon.toFixed(6)}{' '}
                    <a
                      href={`https://www.google.com/maps/search/?api=1&query=${lead.lat},${lead.lon}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="ml-2 text-blue-600 underline text-xs"
                    >
                      View on Google Maps
                    </a>
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Raw Tag Inspection */}
          <div className="modal-section">
            <h4 className="modal-section-title">
              <Layers className="w-3.5 h-3.5 inline mr-1 text-slate-400" />
              Documented OSM Tags
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
                        <td className="font-mono text-xs text-slate-600">{k}</td>
                        <td className="text-xs text-slate-800">{v}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <p className="text-xs text-slate-400 italic">No additional tags recorded.</p>
            )}
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
            Open in OpenStreetMap.org
            <ExternalLink className="w-3.5 h-3.5 ml-1 inline" />
          </a>
          <button type="button" className="btn btn-primary text-xs" onClick={onClose}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

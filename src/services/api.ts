import { CategoryItem, SearchResponse, BusinessLead } from '../types';

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '') + '/api';

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
    this.name = 'ApiError';
  }
}

export async function fetchHealth(): Promise<{ status: string; service: string }> {
  const resp = await fetch(`${API_BASE_URL}/health`);
  if (!resp.ok) {
    throw new ApiError('Service health check failed', resp.status);
  }
  return resp.json();
}

export async function fetchCategories(): Promise<CategoryItem[]> {
  const resp = await fetch(`${API_BASE_URL}/categories`);
  if (!resp.ok) {
    const errorData = await resp.json().catch(() => ({}));
    throw new ApiError(errorData.detail || 'Failed to load business categories', resp.status);
  }
  return resp.json();
}

export async function searchLeads(location: string, category: string): Promise<SearchResponse> {
  const params = new URLSearchParams({
    location: location.trim(),
    category: category.trim(),
  });

  const resp = await fetch(`${API_BASE_URL}/search?${params.toString()}`);
  if (!resp.ok) {
    const errorData = await resp.json().catch(() => ({}));
    throw new ApiError(errorData.detail || `Search failed (HTTP ${resp.status})`, resp.status);
  }
  return resp.json();
}

export async function downloadFilteredLeadsCsv(
  location: string,
  category: string,
  listings: BusinessLead[]
): Promise<void> {
  const resp = await fetch(`${API_BASE_URL}/export-filtered`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      location,
      category,
      listings,
    }),
  });

  if (!resp.ok) {
    const errorData = await resp.json().catch(() => ({}));
    throw new ApiError(errorData.detail || 'Failed to export CSV', resp.status);
  }

  const blob = await resp.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  const cleanLoc = location.toLowerCase().replace(/[^a-z0-9_-]/g, '_');
  a.download = `leads_${cleanLoc}_${category}_filtered.csv`;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}

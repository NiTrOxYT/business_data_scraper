import { CategoryItem, SearchResponse, BusinessLead, SearchJob } from '../types';

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

export async function fetchJobs(): Promise<SearchJob[]> {
  const resp = await fetch(`${API_BASE_URL}/jobs`);
  if (!resp.ok) {
    const errorData = await resp.json().catch(() => ({}));
    throw new ApiError(errorData.detail || 'Failed to load search jobs', resp.status);
  }
  return resp.json();
}

export async function searchLeads(
  location: string,
  category: string,
  keyword?: string,
  radiusKm?: number,
  refresh: boolean = false,
  limit: number = 100
): Promise<SearchResponse> {
  const params = new URLSearchParams({
    location: location.trim(),
    category: category.trim(),
    limit: String(limit),
  });

  if (keyword && keyword.trim()) {
    params.set('keyword', keyword.trim());
  }

  if (radiusKm && radiusKm > 0) {
    params.set('radius_km', String(radiusKm));
  }

  if (refresh) {
    params.set('refresh', 'true');
  }

  const resp = await fetch(`${API_BASE_URL}/search?${params.toString()}`);
  if (!resp.ok) {
    const errorData = await resp.json().catch(() => ({}));
    throw new ApiError(errorData.detail || `Search failed (HTTP ${resp.status})`, resp.status);
  }
  return resp.json();
}

export async function downloadFilteredLeads(
  location: string,
  category: string,
  listings: BusinessLead[],
  format: 'csv' | 'excel' = 'csv'
): Promise<void> {
  const resp = await fetch(`${API_BASE_URL}/export-filtered`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      location,
      category,
      format,
      listings,
    }),
  });

  if (!resp.ok) {
    const errorData = await resp.json().catch(() => ({}));
    throw new ApiError(errorData.detail || `Failed to export ${format.toUpperCase()}`, resp.status);
  }

  const blob = await resp.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  const cleanLoc = location.toLowerCase().replace(/[^a-z0-9_-]/g, '_');
  const extension = format === 'excel' ? 'xlsx' : 'csv';
  a.download = `leads_${cleanLoc}_${category}_filtered.${extension}`;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}

export async function downloadExport(
  location: string,
  category: string,
  keyword?: string,
  radiusKm?: number,
  limit: number = 100,
  refresh: boolean = false,
  format: 'csv' | 'excel' = 'csv'
): Promise<void> {
  const params = new URLSearchParams({
    location: location.trim(),
    category: category.trim(),
    limit: String(limit),
    format,
  });

  if (keyword && keyword.trim()) {
    params.set('keyword', keyword.trim());
  }
  if (radiusKm && radiusKm > 0) {
    params.set('radius_km', String(radiusKm));
  }
  if (refresh) {
    params.set('refresh', 'true');
  }

  const resp = await fetch(`${API_BASE_URL}/export?${params.toString()}`);
  if (!resp.ok) {
    const errorData = await resp.json().catch(() => ({}));
    throw new ApiError(errorData.detail || `Failed to download export (HTTP ${resp.status})`, resp.status);
  }

  const blob = await resp.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  const cleanLoc = location.toLowerCase().replace(/[^a-z0-9_-]/g, '_');
  const extension = format === 'excel' ? 'xlsx' : 'csv';
  a.download = `leads_${cleanLoc}_${category}.${extension}`;
  document.body.appendChild(a);
  a.click();
  window.URL.revokeObjectURL(url);
  document.body.removeChild(a);
}

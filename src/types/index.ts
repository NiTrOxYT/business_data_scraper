export interface CategoryItem {
  id: string;
  label: string;
  description: string;
  display_tags: string[];
}

export interface BusinessLead {
  id: string;
  name: string;
  category: string;
  category_label: string;
  phone: string;
  website: string;
  email: string;
  address: string;
  city: string;
  postcode: string;
  lat: number | null;
  lon: number | null;
  osm_type: string;
  osm_id: number;
  osm_url: string;
  data_source: string;
  search_timestamp: string;
  tags: Record<string, string>;
}

export interface SearchDiagnostics {
  cache_hit: boolean;
  data_source: string;
  upstream_count: number;
  parsed_count: number;
  deduplicated_count: number;
  final_count: number;
  bounding_box: [number, number, number, number];
  search_area_type?: string;
  search_area_description?: string;
  center_coordinates?: [number, number];
  radius_km?: number | null;
  resolved_location?: string;
}

export interface SearchResponse {
  location: string;
  resolved_location: string;
  category: string;
  category_label: string;
  keyword?: string | null;
  radius_km?: number | null;
  bounding_box: [number, number, number, number];
  total_found: number;
  listings: BusinessLead[];
  attribution: string;
  notice: string;
  cached: boolean;
  diagnostics?: SearchDiagnostics;
}

export interface SearchJob {
  id: string;
  status: 'running' | 'completed' | 'failed';
  location: string;
  category: string;
  category_label: string;
  keyword?: string | null;
  radius_km?: number | null;
  limit: number;
  started_at: string;
  completed_at?: string | null;
  duration_seconds?: number | null;
  records_found: number;
  duplicates_removed: number;
  data_source: string;
  cached: boolean;
  error?: string | null;
}

export interface FilterState {
  keyword: string;
  phoneOnly: boolean;
  websiteOnly: boolean;
  emailOnly: boolean;
  addressOnly: boolean;
  sortBy: 'name' | 'city' | 'phone' | 'website';
  sortOrder: 'asc' | 'desc';
}

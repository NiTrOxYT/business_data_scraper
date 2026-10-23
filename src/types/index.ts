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
  address: string;
  city: string;
  postcode: string;
  lat: number | null;
  lon: number | null;
  osm_type: string;
  osm_id: number;
  osm_url: string;
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
}

export interface SearchResponse {
  location: string;
  resolved_location: string;
  category: string;
  category_label: string;
  bounding_box: [number, number, number, number];
  total_found: number;
  listings: BusinessLead[];
  attribution: string;
  notice: string;
  cached: boolean;
  diagnostics?: SearchDiagnostics;
}

export interface FilterState {
  keyword: string;
  phoneOnly: boolean;
  websiteOnly: boolean;
  addressOnly: boolean;
  sortBy: 'name' | 'city' | 'phone' | 'website';
  sortOrder: 'asc' | 'desc';
}

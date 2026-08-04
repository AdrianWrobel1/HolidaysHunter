export interface PriceHistoryResponse {
  id: string;
  price_total: string;
  price_per_person: string;
  recorded_at: string;
}

export interface OfferResponse {
  id: string;
  external_id: string;
  provider: 'itaka' | 'tui' | 'rainbow' | 'wakacje_pl' | string;
  title: string;
  country: string;
  region: string | null;
  city: string | null;
  hotel_name: string;
  hotel_stars: number | null;
  hotel_rating: number | null;
  departure_date: string;
  return_date: string;
  duration_nights: number;
  departure_city: string;
  adults: number;
  children: number;
  meal_type: string;
  transport_type: string;
  price_total: string;
  price_per_person: string;
  currency: string;
  offer_url: string;
  image_url: string | null;
  travel_score: number | null;
  is_available: boolean;
}

export interface OfferDetailResponse extends OfferResponse {
  first_seen_at: string;
  last_seen_at: string;
  price_history: PriceHistoryResponse[];
  price_change_pct: number | null;
  days_available: number;
}

export interface OffersListResponse {
  offers: OfferResponse[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface FilterOptionsResponse {
  countries: string[];
  regions: string[];
  departure_cities: string[];
  providers: string[];
  meal_types: string[];
  transport_types: string[];
}

export interface TravelProfile {
  id: string;
  name: string;
  countries: string[] | null;
  regions: string[] | null;
  departure_cities: string[] | null;
  date_from: string | null;
  date_to: string | null;
  duration_min: number | null;
  duration_max: number | null;
  budget_min: string | null;
  budget_max: string | null;
  adults: number | null;
  children: number | null;
  hotel_stars_min: number | null;
  meal_types: string[] | null;
  providers: string[] | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface TravelProfileCreate {
  name: string;
  countries?: string[];
  regions?: string[];
  departure_cities?: string[];
  date_from?: string;
  date_to?: string;
  duration_min?: number;
  duration_max?: number;
  budget_min?: number;
  budget_max?: number;
  adults?: number;
  children?: number;
  hotel_stars_min?: number;
  meal_types?: string[];
  providers?: string[];
}

export interface AlertEvent {
  id: string;
  offer_id: string;
  profile_id: string | null;
  alert_type: 'new_match' | 'price_drop' | 'lowest_price' | 'high_score' | 'reappeared' | string;
  message: string;
  metadata_json: Record<string, any> | null;
  is_read: boolean;
  triggered_at: string;
}

export interface AlertsListResponse {
  alerts: AlertEvent[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface OfferQueryParams {
  page?: number;
  page_size?: number;
  country?: string;
  region?: string;
  provider?: string;
  departure_city?: string;
  meal_type?: string;
  transport_type?: string;
  hotel_stars_min?: number;
  price_min?: number;
  price_max?: number;
  date_from?: string;
  date_to?: string;
  duration_min?: number;
  duration_max?: number;
  adults?: number;
  children?: number;
  search?: string;
  available_only?: boolean;
  sort_by?: string;
  sort_order?: 'asc' | 'desc';
}

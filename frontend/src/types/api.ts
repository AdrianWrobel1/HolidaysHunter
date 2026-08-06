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
  offer_url: string | null;
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
  country_regions?: Record<string, string[]>;
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
  transport_types?: string[] | null;
  notification_policy?: string;
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
  transport_types?: string[];
  notification_policy?: string;
}

export interface TravelProfileUpdate {
  name?: string;
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
  transport_types?: string[];
  notification_policy?: string;
  is_active?: boolean;
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
  country?: string | string[];
  region?: string | string[];
  provider?: string | string[];
  departure_city?: string | string[];
  meal_type?: string | string[];
  transport_type?: string;
  hotel_stars?: number | number[];
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

// --- OFFER ANALYZER SCHEMAS ---

export interface TargetOfferSummary {
  external_id: string;
  provider: string;
  title: string;
  country: string;
  region?: string | null;
  city?: string | null;
  hotel_name: string;
  hotel_stars?: number | null;
  hotel_rating?: number | null;
  departure_date: string;
  return_date: string;
  duration_nights: number;
  departure_city: string;
  adults: number;
  children: number;
  meal_type: string;
  transport_type: string;
  price_total: number;
  price_per_person: number;
  currency: string;
  offer_url?: string | null;
  image_url?: string | null;
}

export interface SimilarOfferItem {
  id?: string | null;
  external_id: string;
  provider: string;
  title: string;
  hotel_name: string;
  country: string;
  region?: string | null;
  hotel_stars?: number | null;
  departure_date: string;
  duration_nights: number;
  meal_type: string;
  departure_city: string;
  price_per_person: number;
  similarity_score: number;
  explanations: string[];
  offer_url?: string | null;
  transport_type?: string;
}

export interface SimilarityAnalysis {
  candidates_count: number;
  top_matches: SimilarOfferItem[];
}

export interface PriceAnalysis {
  min_price: number;
  max_price: number;
  mean_price: number;
  median_price: number;
  std_dev: number;
  percentile_25: number;
  percentile_75: number;
  target_price: number;
  price_per_day: number;
  price_per_person_per_day: number;
  price_diff_amount: number;
  price_diff_pct: number;
  position_summary: string;
}

export interface MarketPosition {
  cheaper_than_pct: number;
  more_expensive_than_pct: number;
  price_percentile: number;
  rank_position: number;
  total_candidates: number;
  rank_summary: string;
}

export interface PriceEfficiency {
  daily_rate: number;
  person_daily_rate: number;
  market_avg_person_daily_rate: number;
  efficiency_score: number;
  summary: string;
}

export interface OfferQuality {
  quality_score: number;
  completeness_pct: number;
  highlights: string[];
}

export interface ConfidenceScore {
  score: number;
  level: string;
  data_points_count: number;
  has_price_history: boolean;
  completeness_pct: number;
  explanations: string[];
}

export interface DealScoreComponentSchema {
  name: string;
  score: number;
  weight: number;
  weighted_score: number;
  impact?: number;
  explanation?: string | null;
}

export interface DealScoreBreakdown {
  total_score: number;
  raw_score: number;
  summary: string;
  value_score?: number;
  confidence?: ConfidenceScore;
  components: DealScoreComponentSchema[];
  explanations?: string[];
}

export interface Recommendation {
  verdict_badge: string;
  verdict_color: string;
  title: string;
  takeaways: string[];
}

export interface HistogramBin {
  bin_label: string;
  bin_min: number;
  bin_max: number;
  count: number;
  is_target_bin: boolean;
}

export interface BoxPlotData {
  min_val: number;
  q1: number;
  median: number;
  q3: number;
  max_val: number;
  target_val: number;
}

export interface VisualizationData {
  histogram_bins: HistogramBin[];
  box_plot: BoxPlotData;
  deal_score_breakdown: DealScoreComponentSchema[];
}

export interface OfferAnalysisReport {
  analysis_id: string;
  target_type: string;
  started_at: string;
  finished_at?: string | null;
  duration_ms?: number | null;
  framework_version: string;
  cache_used: boolean;
  target_offer: TargetOfferSummary;
  similarity: SimilarityAnalysis;
  statistics: PriceAnalysis;
  market_position: MarketPosition;
  price_efficiency: PriceEfficiency;
  offer_quality: OfferQuality;
  deal_score: DealScoreBreakdown;
  recommendation: Recommendation;
  charts: VisualizationData;
}

// --- RESEARCH WORKSPACE SCHEMAS ---

export interface SessionResponse {
  id: string;
  name: string;
  description?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  collections_count: number;
  items_count: number;
}

export interface DuplicateCheckResponse {
  is_duplicate: boolean;
  existing_item_id?: string | null;
  existing_session_id?: string | null;
  existing_session_name?: string | null;
  is_in_current_session: boolean;
}

export interface ChangeDelta {
  metric: string;
  old_value: any;
  new_value: any;
  diff_text: string;
  is_positive?: boolean | null;
}

export interface ChangeDetectionReport {
  item_id: string;
  previous_analysis_id?: string | null;
  latest_analysis_id: string;
  compared_at: string;
  deltas: ChangeDelta[];
  summary: string;
}

export interface WorkspaceItemResponse {
  id: string;
  session_id: string;
  collection_id?: string | null;
  offer_url: string;
  offer_id?: string | null;
  is_pinned: boolean;
  tags: string[];
  notes: string[];
  latest_report?: OfferAnalysisReport | null;
  history_count: number;
  change_detection?: ChangeDetectionReport | null;
  created_at: string;
  updated_at: string;
}

export interface ComparisonMatrixRow {
  label: string;
  values: any[];
  best_indices: number[];
}

export interface MultiOfferCompareReport {
  item_ids: string[];
  items: WorkspaceItemResponse[];
  matrix: Record<string, ComparisonMatrixRow>;
  best_overall_index: number;
  best_value_index: number;
  cheapest_index: number;
  highest_standard_index: number;
  upgrade_recommendation: string;
}

// --- SEASONAL ANALYTICS V2 SCHEMAS ---

export interface SeasonalQueryParams {
  country?: string | string[];
  region?: string | string[];
  departure_month?: number | number[];
  travel_length?: number | string;
  duration_min?: number;
  duration_max?: number;
  transport_type?: string | string[];
  meal_type?: string | string[];
  hotel_stars?: number | number[];
  hotel_stars_min?: number;
  hotel_rating_min?: number;
  provider?: string | string[];
  departure_city?: string | string[];
  adults?: number;
  children?: number;
  price_min?: number;
  price_max?: number;
  deal_score_min?: number;
  value_score_min?: number;
  is_last_minute?: boolean;
  is_first_minute?: boolean;
}

export interface SeasonalExecutiveSummary {
  cheapest_month?: {
    month: number;
    name: string;
    season: string;
    avg_price: number;
    min_price: number;
  } | null;
  most_expensive_month?: {
    month: number;
    name: string;
    season: string;
    avg_price: number;
  } | null;
  potential_savings?: {
    amount: number;
    percentage: number;
  } | null;
  best_value_month?: {
    month: number;
    name: string;
    value_score: number;
    avg_price: number;
  } | null;
  biggest_price_drop?: {
    description: string;
    drop_amount: number;
    drop_pct: number;
  } | null;
}

export interface MonthlyHeatmapItem {
  month: number;
  month_name: string;
  season: string;
  avg_price: number;
  median_price: number;
  min_price: number;
  max_price: number;
  p10: number;
  p25: number;
  p75: number;
  p90: number;
  offer_count: number;
  avg_deal_score: number;
  avg_value_score: number;
  price_level: 'low' | 'medium' | 'high';
}

export interface PriceTrendPoint {
  period: string;
  month: number;
  month_name: string;
  avg: number;
  median: number;
  min: number;
  max: number;
  p10: number;
  p25: number;
  p75: number;
  p90: number;
  count: number;
}

export interface DistributionBucket {
  range_min: number;
  range_max: number;
  label: string;
  count: number;
}

export interface BoxPlotData {
  min: number;
  p25: number;
  median: number;
  p75: number;
  max: number;
  mean: number;
}

export interface PriceDistribution {
  buckets: DistributionBucket[];
  box_plot: BoxPlotData;
  market_median: number;
  best_deals_threshold: number;
}

export interface SeasonalityScore {
  score: number;
  level: string;
  description: string;
}

export interface LeadTimeBreakdown {
  window: string;
  avg_price: number;
  count: number;
}

export interface BestTimeToBuy {
  recommendation: 'BUY_NOW' | 'WAIT' | 'TOO_EARLY' | 'TOO_LATE';
  title: string;
  explanation: string;
  estimated_savings_pct: number;
  lead_time_breakdown: LeadTimeBreakdown[];
}

export interface RegionalStat {
  country: string;
  region: string | null;
  avg_price: number;
  median_price: number;
  cheapest_month_name: string;
  most_expensive_month_name: string;
  seasonality_score: number;
  avg_deal_score: number;
  avg_value_score: number;
  offer_count: number;
}

export interface ProviderStat {
  provider: string;
  avg_price: number;
  median_price: number;
  avg_deal_score: number;
  avg_value_score: number;
  cheapest_month_name: string;
  offer_count: number;
}

export interface MonthlyTransportItem {
  month: number;
  month_name: string;
  flight_avg: number;
  self_avg: number;
}

export interface TransportAnalysis {
  flight_avg_price: number | null;
  self_transport_avg_price: number | null;
  flight_premium: number | null;
  transport_split: Record<string, number>;
  monthly_comparison: MonthlyTransportItem[];
}

export interface PriceForecast {
  next_month_name: string;
  expected_price: number;
  confidence_pct: number;
  trend_direction: '↓↓' | '↓' | '→' | '↑' | '↑↑';
  summary: string;
}

export interface EmptyStateDiagnostics {
  has_data: boolean;
  reason?: string | null;
  conflicting_filters: string[];
  suggested_countries: string[];
}

export interface SeasonalAnalyticsResponse {
  total_offers_analyzed: number;
  active_filters: Record<string, any>;
  executive_summary: SeasonalExecutiveSummary;
  monthly_heatmap: MonthlyHeatmapItem[];
  price_trends: PriceTrendPoint[];
  price_distribution: PriceDistribution;
  seasonality_score: SeasonalityScore;
  best_time_to_buy: BestTimeToBuy;
  regional_comparison: RegionalStat[];
  provider_comparison: ProviderStat[];
  transport_analysis: TransportAnalysis;
  price_forecast: PriceForecast;
  smart_insights: string[];
  diagnostics: EmptyStateDiagnostics;
}


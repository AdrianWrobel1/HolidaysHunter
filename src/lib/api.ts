import {
  AlertsListResponse,
  FilterOptionsResponse,
  OfferDetailResponse,
  OfferQueryParams,
  OffersListResponse,
  PriceHistoryResponse,
  TravelProfile,
  TravelProfileCreate,
} from '@/types/api';

const rawApiBaseUrl = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '');
const API_BASE_URL = rawApiBaseUrl.endsWith('/api') ? rawApiBaseUrl : `${rawApiBaseUrl}/api`;

export async function fetchOffers(params: OfferQueryParams = {}): Promise<OffersListResponse> {
  const urlParams = new URLSearchParams();
  
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      if (Array.isArray(value)) {
        value.forEach((v) => {
          if (v !== undefined && v !== null && v !== '') {
            urlParams.append(key, String(v));
          }
        });
      } else {
        urlParams.append(key, String(value));
      }
    }
  });

  const res = await fetch(`${API_BASE_URL}/offers?${urlParams.toString()}`, {
    cache: 'no-store',
  });

  if (!res.ok) {
    throw new Error(`Failed to fetch offers: ${res.statusText}`);
  }

  return res.json();
}

export async function fetchFilterOptions(): Promise<FilterOptionsResponse> {
  const res = await fetch(`${API_BASE_URL}/offers/filters`, {
    cache: 'no-store',
  });

  if (!res.ok) {
    throw new Error(`Failed to fetch filter options: ${res.statusText}`);
  }

  return res.json();
}

export async function fetchOfferDetail(id: string): Promise<OfferDetailResponse> {
  const res = await fetch(`${API_BASE_URL}/offers/${id}`, {
    cache: 'no-store',
  });

  if (!res.ok) {
    throw new Error(`Failed to fetch offer details: ${res.statusText}`);
  }

  return res.json();
}

export async function fetchPriceHistory(id: string): Promise<PriceHistoryResponse[]> {
  const res = await fetch(`${API_BASE_URL}/offers/${id}/price-history`, {
    cache: 'no-store',
  });

  if (!res.ok) {
    throw new Error(`Failed to fetch price history: ${res.statusText}`);
  }

  return res.json();
}

export async function fetchTravelProfiles(): Promise<TravelProfile[]> {
  const res = await fetch(`${API_BASE_URL}/profiles`, {
    cache: 'no-store',
  });

  if (!res.ok) {
    throw new Error(`Failed to fetch profiles: ${res.statusText}`);
  }

  return res.json();
}

export async function fetchLiveOffers(params: OfferQueryParams = {}): Promise<{ status: string; message: string; imported_providers: string[] }> {
  const urlParams = new URLSearchParams();
  
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      if (Array.isArray(value)) {
        value.forEach((v) => {
          if (v !== undefined && v !== null && v !== '') {
            urlParams.append(key, String(v));
          }
        });
      } else {
        urlParams.append(key, String(value));
      }
    }
  });

  const res = await fetch(`${API_BASE_URL}/offers/fetch-live?${urlParams.toString()}`, {
    method: 'POST',
    cache: 'no-store',
  });

  if (!res.ok) {
    throw new Error(`Failed to fetch live offers: ${res.statusText}`);
  }

  return res.json();
}

export async function createTravelProfile(data: TravelProfileCreate): Promise<TravelProfile> {
  const res = await fetch(`${API_BASE_URL}/profiles`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    throw new Error(`Failed to create profile: ${res.statusText}`);
  }

  return res.json();
}

export async function updateTravelProfile(id: string, data: Partial<TravelProfileCreate>): Promise<TravelProfile> {
  const res = await fetch(`${API_BASE_URL}/profiles/${id}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    throw new Error(`Failed to update profile: ${res.statusText}`);
  }

  return res.json();
}

export async function deleteTravelProfile(id: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/profiles/${id}`, {
    method: 'DELETE',
  });

  if (!res.ok) {
    throw new Error(`Failed to delete profile: ${res.statusText}`);
  }
}

export async function fetchAlerts(unreadOnly = false): Promise<AlertsListResponse> {
  const res = await fetch(`${API_BASE_URL}/alerts?unread_only=${unreadOnly}`, {
    cache: 'no-store',
  });

  if (!res.ok) {
    throw new Error(`Failed to fetch alerts: ${res.statusText}`);
  }

  return res.json();
}

export async function markAlertRead(id: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/alerts/${id}/read`, {
    method: 'PATCH',
  });

  if (!res.ok) {
    throw new Error(`Failed to mark alert as read: ${res.statusText}`);
  }
}

export async function markAllAlertsRead(): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/alerts/read-all`, {
    method: 'POST',
  });

  if (!res.ok) {
    throw new Error(`Failed to mark all alerts as read: ${res.statusText}`);
  }
}

export async function fetchTelegramStatus(): Promise<{ enabled: boolean; configured: boolean }> {
  const res = await fetch(`${API_BASE_URL}/alerts/telegram/status`, {
    cache: 'no-store',
  });

  if (!res.ok) {
    return { enabled: true, configured: false };
  }

  return res.json();
}

export async function toggleTelegramNotifications(enabled: boolean): Promise<{ enabled: boolean; message: string }> {
  const res = await fetch(`${API_BASE_URL}/alerts/telegram/toggle?enabled=${enabled}`, {
    method: 'POST',
  });

  if (!res.ok) {
    throw new Error(`Failed to toggle Telegram notifications: ${res.statusText}`);
  }

  return res.json();
}

export async function fetchSeasonalTrends(country?: string, region?: string): Promise<Array<{
  country: string;
  region: string;
  month: number;
  month_name: string;
  season: string;
  avg_price: number;
  min_price: number;
  max_price: number;
  offer_count: number;
}>> {
  const params = new URLSearchParams();
  if (country) params.append('country', country);
  if (region) params.append('region', region);

  const queryString = params.toString() ? `?${params.toString()}` : '';
  const res = await fetch(`${API_BASE_URL}/offers/seasonal-trends${queryString}`, {
    cache: 'no-store',
  });

  if (!res.ok) {
    throw new Error(`Failed to fetch seasonal trends: ${res.statusText}`);
  }

  return res.json();
}

export async function deleteOffer(id: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/offers/${id}`, {
    method: 'DELETE',
  });

  if (!res.ok) {
    throw new Error(`Failed to delete offer: ${res.statusText}`);
  }
}

export async function clearAllOffers(): Promise<{ count: number; message: string }> {
  const res = await fetch(`${API_BASE_URL}/offers/clear-all`, {
    method: 'DELETE',
  });

  if (!res.ok) {
    throw new Error(`Failed to clear all offers: ${res.statusText}`);
  }

  return res.json();
}

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

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

export async function fetchOffers(params: OfferQueryParams = {}): Promise<OffersListResponse> {
  const urlParams = new URLSearchParams();
  
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      urlParams.append(key, String(value));
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

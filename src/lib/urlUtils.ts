import { OfferResponse } from '@/types/api';

const PROVIDER_DOMAINS: Record<string, string> = {
  itaka: 'https://www.itaka.pl',
  tui: 'https://www.tui.pl',
  rainbow: 'https://r.pl',
  wakacje_pl: 'https://www.wakacje.pl',
};

/**
 * Resolves the direct booking URL for an offer.
 * Returns the exact offer URL if available, adding the provider domain if relative.
 * Returns null if no valid offer URL is available. No fallbacks (no Google Search, no search query, no region pages).
 */
export function resolveOfferBookingUrl(offer: OfferResponse): string | null {
  if (!offer.offer_url || !offer.offer_url.trim()) {
    return null;
  }

  const url = offer.offer_url.trim();

  if (url.startsWith('http://') || url.startsWith('https://')) {
    return url;
  }

  const provider = (offer.provider || '').toLowerCase();
  const domain = PROVIDER_DOMAINS[provider];

  if (domain) {
    return url.startsWith('/') ? `${domain}${url}` : `${domain}/${url}`;
  }

  return url;
}

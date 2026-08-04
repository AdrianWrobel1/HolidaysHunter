import { OfferResponse } from '@/types/api';

/**
 * Resolves a valid external booking URL for an offer.
 * If the provided offer_url is missing or invalid, generates a targeted search URL
 * on the provider's website or Google so the user can easily find and book the offer.
 */
export function resolveOfferBookingUrl(offer: OfferResponse): string {
  const rawUrl = offer.offer_url ? offer.offer_url.trim() : '';

  if (rawUrl.startsWith('http://') || rawUrl.startsWith('https://')) {
    return rawUrl;
  }

  const provider = (offer.provider || '').toLowerCase();
  const query = encodeURIComponent(`${offer.hotel_name || ''} ${offer.country || ''}`.trim());

  // Handle relative URLs if any
  if (rawUrl.startsWith('/')) {
    if (provider.includes('itaka')) return `https://www.itaka.pl${rawUrl}`;
    if (provider.includes('tui')) return `https://www.tui.pl${rawUrl}`;
    if (provider.includes('rainbow')) return `https://r.pl${rawUrl}`;
    if (provider.includes('wakacje')) return `https://www.wakacje.pl${rawUrl}`;
  }

  // Fallback search URLs per provider
  if (provider.includes('itaka')) {
    return query ? `https://www.itaka.pl/wyniki-wyszukiwania/?q=${query}` : 'https://www.itaka.pl';
  }
  if (provider.includes('tui')) {
    return query ? `https://www.tui.pl/wyszukiwanie?query=${query}` : 'https://www.tui.pl';
  }
  if (provider.includes('rainbow')) {
    return query ? `https://r.pl/szukaj?q=${query}` : 'https://r.pl';
  }
  if (provider.includes('wakacje')) {
    return query ? `https://www.wakacje.pl/oferty/?q=${query}` : 'https://www.wakacje.pl';
  }

  // General web search fallback
  return `https://www.google.com/search?q=${encodeURIComponent(`${offer.provider || ''} ${offer.hotel_name || ''} ${offer.country || ''} rezerwacja wakacje`.trim())}`;
}

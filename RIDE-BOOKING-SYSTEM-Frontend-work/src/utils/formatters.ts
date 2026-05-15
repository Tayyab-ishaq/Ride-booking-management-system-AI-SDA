// Currency formatter — defaults to PKR for this app
export const formatCurrency = (amount: number, currency = 'PKR') =>
  new Intl.NumberFormat('en-PK', { style: 'currency', currency }).format(amount);

// Distance: meters → "1.4 km" or "300 m"
export const formatDistance = (meters: number) =>
  meters >= 1000 ? `${(meters / 1000).toFixed(1)} km` : `${Math.round(meters)} m`;

// Duration: seconds → "5 min" or "1 hr 12 min"
export const formatDuration = (seconds: number) => {
  const m = Math.round(seconds / 60);
  if (m < 60) return `${m} min`;
  const h = Math.floor(m / 60);
  const rem = m % 60;
  return rem > 0 ? `${h} hr ${rem} min` : `${h} hr`;
};

// Short date: "Apr 24, 2026"
export const formatDate = (dateStr: string) =>
  new Date(dateStr).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });

// Short time: "3:42 PM"
export const formatTime = (dateStr: string) =>
  new Date(dateStr).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true });

// Rating: 4.8 → "4.8 ★"
export const formatRating = (rating: number) => `${Number(rating).toFixed(1)} ★`;

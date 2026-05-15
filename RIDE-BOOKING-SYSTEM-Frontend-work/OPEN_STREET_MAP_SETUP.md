# OpenStreetMap Setup Guide (No API Key)

This project now uses OpenStreetMap tiles with Leaflet and Nominatim.
You do not need a Google API key or billing card.

## What is used

1. OpenStreetMap tile server for map rendering
2. Leaflet + react-leaflet for map UI
3. Nominatim for address search and reverse geocoding

## Prerequisites

Install dependencies in frontend workspace:

```bash
pnpm add leaflet react-leaflet
pnpm add -D @types/leaflet
```

## No env variable required

Remove or ignore this old variable if present:

```bash
VITE_GOOGLE_MAPS_API_KEY=...
```

The current OSM flow works without API keys.

## Run and test

```bash
pnpm dev
```

Then verify in the app:

1. Open the location picker page/component
2. Search an address in the input and select a result
3. Click on the map to pick coordinates directly
4. Click Auto-detect to use browser GPS
5. Confirm latitude and longitude are shown and sent in payload

## Data behavior

1. Driver location is stored in `driver_locations` as latitude/longitude
2. Rider pickup/dropoff can be saved through existing ride creation flow

## Notes for production

1. Public Nominatim has usage limits and policy requirements
2. Add request throttling/debouncing for search calls
3. For high traffic, migrate geocoding to a managed provider or self-hosted service
4. Keep OpenStreetMap attribution visible in the map UI

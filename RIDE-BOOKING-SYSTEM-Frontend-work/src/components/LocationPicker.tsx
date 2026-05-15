import { useMemo, useState } from "react";
import {
  MapContainer,
  Marker,
  TileLayer,
  useMapEvents,
} from "react-leaflet";
import L, { LeafletMouseEvent } from "leaflet";
import "leaflet/dist/leaflet.css";

export interface LocationData {
  latitude: number;
  longitude: number;
  address: string;
}

interface LocationPickerProps {
  onLocationSelect: (location: LocationData) => void;
  placeholder?: string;
}

type SearchResult = {
  display_name: string;
  lat: string;
  lon: string;
};

const defaultCenter: [number, number] = [31.5204, 74.3587];

const markerIcon = L.icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  iconRetinaUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

function ClickHandler({ onPick }: { onPick: (lat: number, lon: number) => void }) {
  useMapEvents({
    click(event: LeafletMouseEvent) {
      onPick(event.latlng.lat, event.latlng.lng);
    },
  });

  return null;
}

export const LocationPicker = ({
  onLocationSelect,
  placeholder = "Enter location",
}: LocationPickerProps) => {
  const [location, setLocation] = useState<LocationData | null>(null);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const mapCenter = useMemo<[number, number]>(() => {
    if (!location) return defaultCenter;
    return [location.latitude, location.longitude];
  }, [location]);

  const applyLocation = (newLocation: LocationData) => {
    setLocation(newLocation);
    setQuery(newLocation.address);
    setResults([]);
    onLocationSelect(newLocation);
    setError("");
  };

  const reverseGeocode = async (lat: number, lon: number): Promise<string> => {
    const res = await fetch(
      `https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat=${lat}&lon=${lon}`,
      {
        headers: {
          Accept: "application/json",
        },
      }
    );

    if (!res.ok) {
      throw new Error("Unable to resolve address for this coordinate");
    }

    const data = await res.json();
    return data.display_name || `${lat.toFixed(6)}, ${lon.toFixed(6)}`;
  };

  const handleMapPick = async (lat: number, lon: number) => {
    setLoading(true);
    try {
      const address = await reverseGeocode(lat, lon);
      applyLocation({ latitude: lat, longitude: lon, address });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Location lookup failed");
      applyLocation({
        latitude: lat,
        longitude: lon,
        address: `${lat.toFixed(6)}, ${lon.toFixed(6)}`,
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    const trimmed = query.trim();
    if (!trimmed) {
      setResults([]);
      return;
    }

    setLoading(true);
    setError("");

    try {
      const url = `https://nominatim.openstreetmap.org/search?format=jsonv2&limit=5&q=${encodeURIComponent(trimmed)}`;
      const res = await fetch(url, {
        headers: {
          Accept: "application/json",
        },
      });

      if (!res.ok) {
        throw new Error("Search failed. Please try again.");
      }

      const data: SearchResult[] = await res.json();
      setResults(data);
      if (data.length === 0) {
        setError("No location found. Try a different search term.");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setLoading(false);
    }
  };

  const handleChooseResult = (item: SearchResult) => {
    applyLocation({
      latitude: Number(item.lat),
      longitude: Number(item.lon),
      address: item.display_name,
    });
  };

  // Auto-detect current location
  const handleAutoDetect = async () => {
    setLoading(true);
    setError("");

    if (!navigator.geolocation) {
      setError("Geolocation not supported by your browser");
      setLoading(false);
      return;
    }

    try {
      const position = await new Promise<GeolocationPosition>(
        (resolve, reject) => {
          navigator.geolocation.getCurrentPosition(resolve, reject, {
            enableHighAccuracy: false,
            timeout: 30000,
            maximumAge: 60000,
          });
        }
      );

      const { latitude, longitude } = position.coords;
      const address = await reverseGeocode(latitude, longitude);
      applyLocation({ latitude, longitude, address });
    } catch (err: any) {
      setError(
        err.message || "Could not detect location. Check browser permissions."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-md mx-auto">
      <div className="bg-white rounded-lg shadow-md p-4">
        {/* Address Input with Google Places Autocomplete */}
        <div className="mb-3">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            📍 Location
          </label>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder={placeholder}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
            />
            <button
              type="button"
              onClick={handleSearch}
              disabled={loading}
              className="px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-800 disabled:bg-gray-400"
            >
              Search
            </button>
          </div>
          {results.length > 0 && (
            <ul className="mt-2 max-h-44 overflow-auto rounded-lg border border-gray-200 bg-white">
              {results.map((item) => (
                <li key={`${item.lat}-${item.lon}`}>
                  <button
                    type="button"
                    onClick={() => handleChooseResult(item)}
                    className="w-full text-left px-3 py-2 text-sm hover:bg-gray-100"
                  >
                    {item.display_name}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        <div className="mb-3 h-64 overflow-hidden rounded-lg border border-gray-300">
          <MapContainer center={mapCenter} zoom={13} className="h-full w-full">
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <ClickHandler onPick={handleMapPick} />
            {location && (
              <Marker position={[location.latitude, location.longitude]} icon={markerIcon} />
            )}
          </MapContainer>
        </div>

        {/* Auto-detect Button */}
        <button
          onClick={handleAutoDetect}
          disabled={loading}
          className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition font-medium"
        >
          {loading ? "🔍 Detecting..." : "📡 Auto-detect Current Location"}
        </button>

        {/* Display Selected Location */}
        {location && (
          <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
            <p className="text-xs font-semibold text-green-800 mb-2">
              ✅ Location Selected
            </p>
            <div className="text-sm text-gray-700 space-y-1">
              <p>
                <span className="font-medium">Address:</span> {location.address}
              </p>
              <p>
                <span className="font-medium">Latitude:</span>{" "}
                {location.latitude.toFixed(6)}
              </p>
              <p>
                <span className="font-medium">Longitude:</span>{" "}
                {location.longitude.toFixed(6)}
              </p>
            </div>

            {/* OpenStreetMap Link */}
            <a
              href={`https://www.openstreetmap.org/?mlat=${location.latitude}&mlon=${location.longitude}#map=16/${location.latitude}/${location.longitude}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-blue-600 hover:underline mt-2 inline-block"
            >
              View on OpenStreetMap →
            </a>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-700">❌ {error}</p>
          </div>
        )}

        {/* Info */}
        <p className="text-xs text-gray-500 mt-4">
          💡 Search an address or click "Auto-detect" to use your GPS location
        </p>
      </div>
    </div>
  );
};

export default LocationPicker;

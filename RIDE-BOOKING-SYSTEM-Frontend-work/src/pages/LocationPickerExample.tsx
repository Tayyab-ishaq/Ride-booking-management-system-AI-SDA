import { useState } from "react";
import LocationPicker, { LocationData } from "../components/LocationPicker";
import { tokenStorage } from "../utils/tokenStorage";

/**
 * EXAMPLE: How to use LocationPicker component
 * Shows integration for both drivers and riders
 */

export const LocationPickerExample = () => {
  const [driverLocation, setDriverLocation] = useState<LocationData | null>(null);
  const [riderPickup, setRiderPickup] = useState<LocationData | null>(null);
  const [riderDropoff, setRiderDropoff] = useState<LocationData | null>(null);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  // Save driver's location to backend
  const handleSaveDriverLocation = async () => {
    if (!driverLocation) {
      setMessage("❌ Please select a location first");
      return;
    }

    setSaving(true);
    try {
      const response = await fetch("/api/driver/save-location", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${tokenStorage.getAccess() ?? ""}`,
        },
        body: JSON.stringify({
          latitude: driverLocation.latitude,
          longitude: driverLocation.longitude,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setMessage(`✅ Driver location saved! ID: ${data.loc_id}`);
      } else {
        setMessage("❌ Failed to save driver location");
      }
    } catch (error) {
      setMessage(`❌ Error: ${error}`);
    }
    setSaving(false);
  };

  // For riders - these are typically saved when creating a ride
  const handleSaveRideLocations = async () => {
    if (!riderPickup || !riderDropoff) {
      setMessage("❌ Please select both pickup and dropoff locations");
      return;
    }

    setSaving(true);
    try {
      const response = await fetch("/api/rides/create", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${tokenStorage.getAccess() ?? ""}`,
        },
        body: JSON.stringify({
          origin: riderPickup.address,
          destination: riderDropoff.address,
          origin_lat: riderPickup.latitude,
          origin_lng: riderPickup.longitude,
          dest_lat: riderDropoff.latitude,
          dest_lng: riderDropoff.longitude,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setMessage(`✅ Ride created! ID: ${data.ride_id}`);
      } else {
        setMessage("❌ Failed to create ride");
      }
    } catch (error) {
      setMessage(`❌ Error: ${error}`);
    }
    setSaving(false);
  };

  return (
    <div className="min-h-screen bg-gray-100 p-6">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Location Picker Examples</h1>

        {/* Status Message */}
        {message && (
          <div className={`p-4 rounded-lg mb-6 text-white font-medium ${
            message.includes("✅") ? "bg-green-600" : "bg-red-600"
          }`}>
            {message}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* DRIVER SECTION */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-2xl font-bold mb-4 flex items-center">
              🚗 Driver Location
            </h2>

            <LocationPicker
              onLocationSelect={(location) => {
                setDriverLocation(location);
                setMessage("");
              }}
              placeholder="Enter your service location"
            />

            <button
              onClick={handleSaveDriverLocation}
              disabled={!driverLocation || saving}
              className="w-full mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition font-medium"
            >
              {saving ? "Saving..." : "💾 Save My Service Location"}
            </button>

            {driverLocation && (
              <div className="mt-4 p-3 bg-blue-50 rounded-lg text-sm">
                <p>
                  <strong>Will save to:</strong> driver_locations table
                </p>
                <p className="text-gray-600 text-xs mt-1">
                  This is where you operate your service
                </p>
              </div>
            )}
          </div>

          {/* RIDER SECTION */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-2xl font-bold mb-4 flex items-center">
              👤 Rider Locations
            </h2>

            <div className="space-y-4">
              {/* Pickup Location */}
              <div>
                <label className="block font-semibold mb-2">
                  📍 Pickup Location
                </label>
                <LocationPicker
                  onLocationSelect={(location) => {
                    setRiderPickup(location);
                    setMessage("");
                  }}
                  placeholder="Where to pick me up?"
                />
              </div>

              {/* Dropoff Location */}
              <div>
                <label className="block font-semibold mb-2">
                  🏁 Dropoff Location
                </label>
                <LocationPicker
                  onLocationSelect={(location) => {
                    setRiderDropoff(location);
                    setMessage("");
                  }}
                  placeholder="Where to drop me off?"
                />
              </div>
            </div>

            <button
              onClick={handleSaveRideLocations}
              disabled={!riderPickup || !riderDropoff || saving}
              className="w-full mt-4 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:bg-gray-400 transition font-medium"
            >
              {saving ? "Creating..." : "📤 Request a Ride"}
            </button>

            {riderPickup && riderDropoff && (
              <div className="mt-4 p-3 bg-green-50 rounded-lg text-sm">
                <p>
                  <strong>Will save to:</strong> rides table
                </p>
                <p>From: {riderPickup.address}</p>
                <p>To: {riderDropoff.address}</p>
              </div>
            )}
          </div>
        </div>

        {/* INFO BOX */}
        <div className="mt-8 bg-amber-50 border-2 border-amber-200 rounded-lg p-6">
          <h3 className="text-lg font-bold text-amber-900 mb-3">
            📚 How It Works
          </h3>
          <ul className="space-y-2 text-amber-800 text-sm">
            <li>✓ Search for an address using OpenStreetMap</li>
            <li>✓ Or click "Auto-detect" to use your GPS location</li>
            <li>✓ Coordinates automatically captured as latitude/longitude</li>
            <li>✓ Driver locations stored in: <code className="bg-white px-2 py-1 rounded">driver_locations</code> table</li>
            <li>✓ Rider locations stored in: <code className="bg-white px-2 py-1 rounded">rides</code> table (origin/destination)</li>
            <li>✓ All locations stored with precise coordinates</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default LocationPickerExample;

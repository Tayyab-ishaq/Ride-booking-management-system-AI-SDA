import { useEffect, useState, useRef } from 'react';
import { useSocketContext } from '../../context/SocketContext';
import { Car, DollarSign, TrendingUp, Phone, MessageSquare, Navigation, CheckCircle, XCircle, Clock, Star, User, FileText } from 'lucide-react';
import ProfilePage from '../ProfilePage';
import { MapView } from '../../components/map/RideMap';
import { useDriverLocation } from '../../hooks/useDriverLocation';
import { driverApi } from '../../api/driverApi';
import { matchingApi } from '../../api/matchingApi';
import { rideApi } from '../../api/rideApi';
import { useAuthContext } from '../../context/AuthContext';

type DriverScreen = 'home' | 'incoming' | 'active' | 'earnings' | 'profile';

type DriverDashboard = {
  todayEarnings: number;
  ridesToday: number;
  bonusRemaining: number;
  totalEarnings: number;
  totalTrips: number;
  averageFare: number;
  recentTrips: Array<{
    id: string;
    time: string;
    route: string;
    fare: number;
    rating: number | null;
  }>;
};

export function DriverPortal() {
  const PENDING_OFFER_STORAGE_KEY = 'driver_pending_offer';
  const [screen, setScreen] = useState<DriverScreen>('home');
  const [isOnline, setIsOnline] = useState(true);
  const [incomingRide, setIncomingRide] = useState<any>(null);
  const [activeRide, setActiveRide] = useState<any>(null);
  const [loadingIncomingRide, setLoadingIncomingRide] = useState(false);
  const [dashboardLoading, setDashboardLoading] = useState(false);
  const [dashboardError, setDashboardError] = useState<string | null>(null);
  const [dashboard, setDashboard] = useState<DriverDashboard>({
    todayEarnings: 0,
    ridesToday: 0,
    bonusRemaining: 3,
    totalEarnings: 0,
    totalTrips: 0,
    averageFare: 0,
    recentTrips: [],
  });
  const { driverSocket } = useSocketContext();
  const { user } = useAuthContext();
  const getRideId = (ride: any) => String(ride?.ride_id ?? ride?.id ?? '');
  const RIDE_COMPARE_FIELDS = [
    'id',
    'ride_id',
    'status',
    'rider_id',
    'rider_full_name',
    'origin',
    'destination',
    'pickup_latitude',
    'pickup_longitude',
    'dropoff_latitude',
    'dropoff_longitude',
    'fare',
    'rating',
  ];
  const ridePayloadsEqual = (a: any, b: any) => {
    if (a === b) return true;
    if (!a || !b) return false;
    for (const key of RIDE_COMPARE_FIELDS) {
      const av = a[key];
      const bv = b[key];
      if (av === bv) continue;
      if (av == null && bv == null) continue;
      return false;
    }
    return true;
  };
  const upsertIncomingRide = (nextRide: any) => {
    if (!nextRide) return;
    setIncomingRide((currentRide: any) => {
      if (!currentRide) return nextRide;

      const currentRideId = getRideId(currentRide);
      const nextRideId = getRideId(nextRide);

      // Keep the currently shown pending offer stable until driver action.
      if (currentRideId && nextRideId && currentRideId !== nextRideId) {
        return currentRide;
      }

      const merged = { ...currentRide, ...nextRide };
      // Skip the state update if nothing meaningful changed — prevents the
      // popup from re-rendering (and flickering) on every poll cycle.
      if (ridePayloadsEqual(currentRide, merged)) {
        return currentRide;
      }
      return merged;
    });
  };

  const startOfDayIso = () => {
    const now = new Date();
    const start = new Date(now);
    start.setHours(0, 0, 0, 0);
    return start.toISOString();
  };

  const todayDateKey = (d: Date) => `${d.getFullYear()}-${d.getMonth()}-${d.getDate()}`;

  const refreshDashboard = async () => {
    if (!user?.id) return;

    setDashboardLoading(true);
    setDashboardError(null);

    try {
      const nowIso = new Date().toISOString();
      const fromIso = startOfDayIso();

      const [overallRes, todayRes, historyRes] = await Promise.all([
        driverApi.earnings(user.id),
        driverApi.earnings(user.id, { from: fromIso, to: nowIso }),
        rideApi.history({ page: 1, page_size: 100 }),
      ]);

      const overall = overallRes?.data ?? {};
      const todaySummary = todayRes?.data ?? {};
      const history = historyRes?.data?.rides ?? [];

      const now = new Date();
      const todayKey = todayDateKey(now);
      const todaysTrips = Array.isArray(history)
        ? history.filter((trip: any) => {
            const createdAt = trip?.created_at ? new Date(trip.created_at) : null;
            if (!createdAt || Number.isNaN(createdAt.getTime())) return false;
            return todayDateKey(createdAt) === todayKey && String(trip?.status ?? '').toLowerCase() === 'completed';
          })
        : [];

      const recentTrips = todaysTrips
        .slice()
        .sort((a: any, b: any) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
        .slice(0, 8)
        .map((trip: any) => ({
          id: String(trip.id),
          time: new Date(trip.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          route: `${trip.origin} -> ${trip.destination}`,
          fare: Number(trip.fare ?? 0),
          rating: trip.rating == null ? null : Number(trip.rating),
        }));

      const ridesToday = Number(todaySummary.completed_rides ?? todaysTrips.length ?? 0);
      const bonusTarget = 3;

      setDashboard({
        todayEarnings: Number(todaySummary.total_earnings ?? 0),
        ridesToday,
        bonusRemaining: Math.max(0, bonusTarget - ridesToday),
        totalEarnings: Number(overall.total_earnings ?? 0),
        totalTrips: Number(overall.completed_rides ?? 0),
        averageFare: Number(overall.average_fare ?? 0),
        recentTrips,
      });
    } catch (e: any) {
      const message = e?.response?.data?.detail ?? e?.message ?? 'Failed to load dashboard data';
      setDashboardError(message);
    } finally {
      setDashboardLoading(false);
    }
  };

  useEffect(() => {
    if (!user?.id) return;

    refreshDashboard();
    const interval = window.setInterval(refreshDashboard, 15000);

    return () => {
      window.clearInterval(interval);
    };
  }, [user?.id]);

  useEffect(() => {
    try {
      const raw = sessionStorage.getItem(PENDING_OFFER_STORAGE_KEY);
      if (!raw) return;
      const restored = JSON.parse(raw);
      if (restored) {
        setIncomingRide(restored);
      }
    } catch {
      // Ignore parse/storage errors and continue with live state.
    }
  }, []);

  useEffect(() => {
    try {
      if (incomingRide) {
        sessionStorage.setItem(PENDING_OFFER_STORAGE_KEY, JSON.stringify(incomingRide));
      } else {
        sessionStorage.removeItem(PENDING_OFFER_STORAGE_KEY);
      }
    } catch {
      // Ignore storage failures; in-memory state is still authoritative.
    }
  }, [incomingRide]);

  useEffect(() => {
    let cancelled = false;

    const markOnline = async () => {
      try {
        await driverApi.setAvailability(true);
      } catch {
        if (!cancelled) {
          // Keep the UI online; backend will retry via the location hook or next refresh.
        }
      }
    };

    markOnline();

    return () => {
      cancelled = true;
    };
  }, []);

  // Sync isOnline from DB on mount — if driver was already available, restore online state
  useEffect(() => {
    driverApi.activeRequest().then(({ data }) => {
      if (data?.ride) {
        setIsOnline(true);
        if (['accepted', 'in_progress'].includes(String(data.ride.status).toLowerCase())) {
          setActiveRide(data.ride);
          setIncomingRide(null);
        } else {
          upsertIncomingRide(data.ride);
        }
      }
    }).catch(() => {});
  }, []);

  // Real-time: subscribe to ride_offer WebSocket event for instant popup
  useEffect(() => {
    if (!driverSocket) return;
    const unsub = driverSocket.onRideOffer((data: any) => {
      if (activeRide) return;
      setIsOnline(true);
      upsertIncomingRide(data);
    });
    const unsubRideCompleted = driverSocket.onRideCompleted((data: any) => {
      const eventRideId = String(data?.ride_id ?? data?.id ?? '');
      setIncomingRide((currentRide: any) => {
        if (!currentRide) return currentRide;
        const currentRideId = getRideId(currentRide);
        return eventRideId && currentRideId === eventRideId ? null : currentRide;
      });
    });
    const unsubRideCancelled = driverSocket.onRideCancelled((data: any) => {
      const eventRideId = String(data?.ride_id ?? data?.id ?? '');
      setIncomingRide((currentRide: any) => {
        if (!currentRide) return currentRide;
        const currentRideId = getRideId(currentRide);
        return eventRideId && currentRideId === eventRideId ? null : currentRide;
      });
    });
    return () => {
      unsub();
      unsubRideCompleted();
      unsubRideCancelled();
    };
  }, [driverSocket, activeRide]);

  // Polling fallback — only while online, no active ride, and no pending offer
  // is on screen. Once an offer arrives (via WS or the first poll), we stop
  // polling so the popup stays stable. WS events (ride_cancelled,
  // ride_completed, status_update) handle teardown from there.
  const hasIncomingRide = !!incomingRide;
  useEffect(() => {
    if (!isOnline) {
      setIncomingRide(null);
      setActiveRide(null);
      setLoadingIncomingRide(false);
      return;
    }

    if (activeRide) {
      setLoadingIncomingRide(false);
      return;
    }

    if (hasIncomingRide) {
      // An offer is already displayed — no need to poll. Driver action,
      // WS events, or a timeout will clear it.
      setLoadingIncomingRide(false);
      return;
    }

    let cancelled = false;
    let firstLoad = true;

    const loadIncomingRide = async () => {
      if (firstLoad) setLoadingIncomingRide(true);
      try {
        const { data } = await driverApi.activeRequest();
        if (cancelled) return;

        const ride = data?.ride ?? null;
        if (!ride) return;

        const normalizedStatus = String(ride.status ?? '').toLowerCase();
        if (normalizedStatus === 'accepted' || normalizedStatus === 'in_progress') {
          setActiveRide((currentRide: any) => currentRide ?? ride);
          setIncomingRide(null);
          return;
        }

        upsertIncomingRide(ride);
      } catch {
        if (!cancelled) {
          setIncomingRide((currentRide: any) => currentRide);
        }
      } finally {
        if (!cancelled && firstLoad) {
          setLoadingIncomingRide(false);
          firstLoad = false;
        }
      }
    };

    loadIncomingRide();
    const interval = window.setInterval(loadIncomingRide, 3000);

    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [isOnline, activeRide, hasIncomingRide]);

  return (
    <div className="size-full flex flex-col overflow-hidden">
      <Header screen={screen} setScreen={setScreen} />

      <div className="flex-1 relative overflow-hidden">
        {screen === 'home' && (
          <HomeScreen
            isOnline={isOnline}
            setScreen={setScreen}
            dashboard={dashboard}
            dashboardLoading={dashboardLoading}
            dashboardError={dashboardError}
          />
        )}
        {screen === 'active' && (
          <ActiveRideScreen
            setScreen={setScreen}
            ride={activeRide ?? incomingRide}
            setActiveRide={setActiveRide}
            setIncomingRide={setIncomingRide}
          />
        )}
        {screen === 'earnings' && (
          <EarningsScreen
            setScreen={setScreen}
            dashboard={dashboard}
            dashboardLoading={dashboardLoading}
            dashboardError={dashboardError}
          />
        )}
        {screen === 'profile' && <ProfileScreen setScreen={setScreen} />}

        {isOnline && incomingRide && (
          <IncomingRequestOverlay
            setScreen={setScreen}
            incomingRide={incomingRide}
            loadingIncomingRide={loadingIncomingRide}
            setIncomingRide={setIncomingRide}
            setActiveRide={setActiveRide}
          />
        )}
      </div>
    </div>
  );
}

function Header({ screen, setScreen }: any) {
  return (
    <header className="h-16 bg-gradient-to-r from-[#12151C] via-[#1A1E28] to-[#12151C] border-b border-[#3B82F6]/20 flex items-center justify-between px-6 z-20">
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2 cursor-pointer" onClick={() => setScreen('home')}>
          <Car className="w-6 h-6 text-[#3B82F6]" />
          <h1 className="text-xl font-bold tracking-tight" style={{ fontFamily: 'var(--font-display)' }}>
            RideFlow Driver
          </h1>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <button onClick={() => setScreen('earnings')} className="p-2 hover:bg-[#1A1E28] rounded-lg transition-colors">
          <DollarSign className="w-5 h-5 text-[#94A3B8]" />
        </button>
        <button onClick={() => setScreen('profile')} className="p-2 hover:bg-[#1A1E28] rounded-lg transition-colors">
          <User className="w-5 h-5 text-[#94A3B8]" />
        </button>
      </div>
    </header>
  );
}

function HomeScreen({ isOnline, setScreen, dashboard, dashboardLoading, dashboardError }: any) {
  const { coords, error } = useDriverLocation(isOnline);

  const lastSentRef = useRef<number>(0);
  const prevCoordsRef = useRef<{ lat: number; lng: number } | null>(null);
  const sendTimerRef = useRef<number | null>(null);

  // Haversine distance (meters)
  const distanceMeters = (a: { lat: number; lng: number }, b: { lat: number; lng: number }) => {
    const toRad = (v: number) => (v * Math.PI) / 180;
    const R = 6371000; // Earth radius in meters
    const dLat = toRad(b.lat - a.lat);
    const dLon = toRad(b.lng - a.lng);
    const lat1 = toRad(a.lat);
    const lat2 = toRad(b.lat);
    const sinDLat = Math.sin(dLat / 2);
    const sinDLon = Math.sin(dLon / 2);
    const val = sinDLat * sinDLat + sinDLon * sinDLon * Math.cos(lat1) * Math.cos(lat2);
    const c = 2 * Math.atan2(Math.sqrt(val), Math.sqrt(1 - val));
    return R * c;
  };

  useEffect(() => {
    const MIN_INTERVAL = 3000; // ms
    const MIN_DISTANCE = 20; // meters

    if (!isOnline || !coords) return;

    const current = { lat: coords.lat, lng: coords.lng };
    const now = Date.now();
    const last = lastSentRef.current || 0;
    const prev = prevCoordsRef.current;

    const shouldSendByTime = now - last >= MIN_INTERVAL;
    const shouldSendByDistance = prev ? distanceMeters(prev, current) >= MIN_DISTANCE : true;

    const send = async () => {
      try {
        await driverApi.updateLocation(current.lat, current.lng);
        lastSentRef.current = Date.now();
        prevCoordsRef.current = current;
      } catch {
        // transient errors are ignored; will retry on next update
      }
    };

    if (shouldSendByTime || shouldSendByDistance) {
      // Clear any scheduled sends
      if (sendTimerRef.current) {
        window.clearTimeout(sendTimerRef.current);
        sendTimerRef.current = null;
      }
      send();
      return;
    }

    // Otherwise schedule a send to happen after remaining interval
    const wait = Math.max(0, MIN_INTERVAL - (now - last));
    if (sendTimerRef.current) {
      window.clearTimeout(sendTimerRef.current);
    }
    sendTimerRef.current = window.setTimeout(() => {
      send();
      sendTimerRef.current = null;
    }, wait);

    return () => {
      if (sendTimerRef.current) {
        window.clearTimeout(sendTimerRef.current);
        sendTimerRef.current = null;
      }
    };
  }, [isOnline, coords]);

  return (
    <>
      <MapView />
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-10">
        <div className="bg-[#12151C] border border-[#1E2433] rounded-2xl p-8 max-w-md w-full shadow-2xl pointer-events-auto">
          <div className="text-center mb-8">
            <div
              className={`relative w-48 h-48 mx-auto rounded-full transition-all duration-500 bg-gradient-to-br from-[#10B981] to-[#059669] shadow-2xl shadow-[#10B981]/50`}
            >
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <div className="text-3xl font-bold mb-2 text-white" style={{ fontFamily: 'var(--font-display)' }}>
                  ONLINE
                </div>
                <div className="text-sm text-white/80">
                  Ready for rides
                </div>
                {error ? <div className="mt-2 text-xs text-red-300">{error}</div> : null}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="bg-[#1A1E28] rounded-xl p-4 border border-[#1E2433]">
              <div className="text-sm text-[#94A3B8] mb-1">Today's Earnings</div>
              <div className="text-2xl font-bold text-[#3B82F6]" style={{ fontFamily: 'var(--font-mono)' }}>
                {dashboardLoading ? '...' : `$${Number(dashboard?.todayEarnings ?? 0).toFixed(2)}`}
              </div>
            </div>
            <div className="bg-[#1A1E28] rounded-xl p-4 border border-[#1E2433]">
              <div className="text-sm text-[#94A3B8] mb-1">Rides Today</div>
              <div className="text-2xl font-bold text-[#3B82F6]" style={{ fontFamily: 'var(--font-mono)' }}>
                {dashboardLoading ? '...' : `${Number(dashboard?.ridesToday ?? 0)} trips`}
              </div>
            </div>
          </div>

          <div className="mt-4 p-4 bg-gradient-to-r from-[#3B82F6]/20 to-[#8B5CF6]/20 border border-[#3B82F6]/30 rounded-xl">
            <div className="text-sm text-[#3B82F6] font-medium">
              {Number(dashboard?.bonusRemaining ?? 0) > 0
                ? `🎯 Complete ${dashboard.bonusRemaining} more ride${dashboard.bonusRemaining === 1 ? '' : 's'} for a $5 bonus!`
                : '🎉 Bonus target achieved for today!'}
            </div>
          </div>
          {dashboardError && <div className="mt-3 text-xs text-[#EF4444]">{dashboardError}</div>}
        </div>
      </div>
    </>
  );
}

function IncomingRequestOverlay({
  setScreen,
  incomingRide,
  loadingIncomingRide,
  setIncomingRide,
  setActiveRide,
}: any) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-[#0A0C10]/95">
      <div className="bg-[#12151C] border-2 border-[#F59E0B] rounded-2xl p-8 max-w-md w-full shadow-2xl shadow-[#F59E0B]/20">
        <div className="text-center mb-6">
          <h2 className="text-2xl font-bold mb-2" style={{ fontFamily: 'var(--font-display)' }}>
            {incomingRide ? 'New Ride Request!' : 'Waiting for ride requests...'}
          </h2>
          {loadingIncomingRide && <p className="text-[#94A3B8] text-sm">Checking for live requests...</p>}
        </div>

        {incomingRide ? (
          <div className="space-y-4 mb-6">
            <div className="bg-[#1A1E28] rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-gradient-to-br from-[#F5A623] to-[#F59E0B] rounded-full flex items-center justify-center text-sm font-bold">
                    {String(incomingRide?.rider_full_name
                      ? String(incomingRide.rider_full_name).slice(0, 2)
                      : (incomingRide.rider_id ?? 'R')).slice(0, 2).toUpperCase()}
                  </div>
                  <div>
                    <div className="font-medium">Ride #{String((incomingRide.ride_id ?? incomingRide.id) ?? '').slice(0, 8)}</div>
                    <div className="text-sm text-[#94A3B8]">{incomingRide?.rider_full_name ?? 'Rider'}</div>
                    <div className="text-sm text-[#94A3B8] flex items-center gap-1">
                      <Star className="w-3 h-3 fill-[#F59E0B] text-[#F59E0B]" />
                      {incomingRide.rating ?? 'New'}
                    </div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-[#3B82F6]" style={{ fontFamily: 'var(--font-mono)' }}>
                    {incomingRide.fare ? `$${Number(incomingRide.fare).toFixed(2)}` : 'Pending'}
                  </div>
                  <div className="text-xs text-[#94A3B8]">Live request</div>
                </div>
              </div>

              <div className="space-y-2 text-sm">
                <div className="flex items-start gap-2">
                  <div className="w-5 h-5 rounded-full bg-[#10B981] flex items-center justify-center text-xs mt-0.5">
                    P
                  </div>
                  <div className="flex-1">
                    <div className="text-[#94A3B8]">Pickup</div>
                    <div>{incomingRide.origin}</div>
                    {incomingRide.pickup_latitude != null && incomingRide.pickup_longitude != null && (
                      <div className="text-xs text-[#64748B] mt-1">
                        {Number(incomingRide.pickup_latitude).toFixed(4)}, {Number(incomingRide.pickup_longitude).toFixed(4)}
                      </div>
                    )}
                  </div>
                </div>
                <div className="flex items-start gap-2">
                  <div className="w-5 h-5 rounded-full bg-[#EF4444] flex items-center justify-center text-xs mt-0.5">
                    D
                  </div>
                  <div className="flex-1">
                    <div className="text-[#94A3B8]">Dropoff</div>
                    <div>{incomingRide.destination}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-4 mb-6">
            <div className="bg-[#1A1E28] rounded-lg p-4 text-center text-[#94A3B8]">
              {loadingIncomingRide ? 'Refreshing live request...' : 'Waiting for the assigned ride to arrive...'}
            </div>
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
          <button
            onClick={async () => {
              const rideId = incomingRide?.ride_id ?? incomingRide?.id;
              if (rideId) {
                  await matchingApi.reject(rideId);
              }
                setIncomingRide(null);
              setScreen('home');
            }}
            className="flex items-center justify-center gap-2 bg-[#1A1E28] hover:bg-[#EF4444]/20 border-2 border-[#EF4444] text-[#EF4444] py-4 rounded-xl font-medium transition-all"
          >
            <XCircle className="w-5 h-5" />
            DECLINE
          </button>
          <button
            onClick={async () => {
                const rideId = incomingRide?.ride_id ?? incomingRide?.id;
                if (rideId) {
                  const { data } = await matchingApi.accept(rideId);
                  setActiveRide(data ?? incomingRide);
              }
                setIncomingRide(null);
              setScreen('active');
            }}
            className="flex items-center justify-center gap-2 bg-[#10B981] hover:bg-[#059669] text-white py-4 rounded-xl font-medium transition-all shadow-lg shadow-[#10B981]/30"
            disabled={!incomingRide}
          >
            <CheckCircle className="w-5 h-5" />
            ACCEPT
          </button>
        </div>

        <div className="mt-4 h-1 bg-[#1E2433] rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-[#10B981] via-[#F59E0B] to-[#EF4444] transition-all duration-1000"
            style={{ width: incomingRide ? '100%' : '35%' }}
          ></div>
        </div>
      </div>
    </div>
  );
}

function ActiveRideScreen({ setScreen, ride, setActiveRide, setIncomingRide }: any) {
  return (
    <>
      <MapView />
      <div className="absolute top-0 left-0 right-0 bg-[#12151C] border-b border-[#1E2433] p-4 z-10 shadow-lg">
        <div className="flex items-center gap-3 bg-[#1A1E28] rounded-lg p-3 border border-[#3B82F6]/30">
          <Navigation className="w-5 h-5 text-[#3B82F6]" />
          <div className="flex-1">
            <div className="text-sm font-medium">Turn right on Shahrah-e-Faisal</div>
            <div className="text-xs text-[#94A3B8]">in 200 meters</div>
          </div>
          <div className="text-right">
            <div className="text-lg font-bold text-[#3B82F6]" style={{ fontFamily: 'var(--font-mono)' }}>
              12 min
            </div>
          </div>
        </div>
      </div>

      <div className="absolute bottom-0 left-0 right-0 bg-[#12151C] border-t border-[#1E2433] p-6 z-10 shadow-2xl">
        <div className="flex items-center gap-4 mb-4">
          <div className="w-14 h-14 bg-gradient-to-br from-[#F5A623] to-[#F59E0B] rounded-full flex items-center justify-center text-lg font-bold">
            {String(ride?.rider_full_name
              ? String(ride.rider_full_name).slice(0, 2)
              : (ride?.rider_id ?? 'R')).slice(0, 2).toUpperCase()}
          </div>
          <div className="flex-1">
            <h3 className="font-medium">{ride ? (ride.rider_full_name ? ride.rider_full_name : `Ride ${String(ride.id).slice(0, 8)}`) : 'Active Ride'}</h3>
            <p className="text-sm text-[#94A3B8]">Pickup: {ride?.origin ?? 'Unknown'}</p>
          </div>
          <div className="text-right">
            <div className="text-xl font-bold text-[#3B82F6]" style={{ fontFamily: 'var(--font-mono)' }}>
              {ride?.fare ? `$${Number(ride.fare).toFixed(2)}` : '—'}
            </div>
            <div className="text-xs text-[#94A3B8]">Running</div>
          </div>
        </div>

        <div className="flex gap-3 mb-4">
          <button className="flex-1 bg-[#1A1E28] hover:bg-[#1E2433] border border-[#1E2433] py-3 rounded-lg flex items-center justify-center gap-2">
            <Phone className="w-5 h-5 text-[#3B82F6]" />
            Call
          </button>
          <button className="flex-1 bg-[#1A1E28] hover:bg-[#1E2433] border border-[#1E2433] py-3 rounded-lg flex items-center justify-center gap-2">
            <MessageSquare className="w-5 h-5 text-[#3B82F6]" />
            Message
          </button>
        </div>

        <button
          onClick={async () => {
            if (!ride?.id) {
              setActiveRide(null);
              setIncomingRide(null);
              setScreen('home');
              return;
            }

            try {
              const latestRide = ride?.status ? ride : (await rideApi.getById(ride.id)).data;
              if (String(latestRide?.status) === 'accepted') {
                await rideApi.start(ride.id);
              }
              await rideApi.complete(ride.id);
            } catch {
              // keep the UI moving even if the backend completion call fails
            } finally {
              setActiveRide(null);
              setIncomingRide(null);
              setScreen('home');
            }
          }}
          className="w-full bg-[#10B981] hover:bg-[#059669] text-white py-4 rounded-lg font-medium shadow-lg"
        >
          Complete Trip
        </button>
      </div>
    </>
  );
}

function EarningsScreen({ setScreen, dashboard, dashboardLoading, dashboardError }: any) {
  const stats = [
    { label: 'Total Earnings', value: `$${Number(dashboard?.totalEarnings ?? 0).toFixed(2)}`, color: 'text-[#3B82F6]' },
    { label: 'Total Trips', value: `${Number(dashboard?.totalTrips ?? 0)}`, color: 'text-[#10B981]' },
    { label: "Today's Earnings", value: `$${Number(dashboard?.todayEarnings ?? 0).toFixed(2)}`, color: 'text-[#F59E0B]' },
    { label: 'Avg. Fare', value: `$${Number(dashboard?.averageFare ?? 0).toFixed(2)}`, color: 'text-[#F5A623]' },
  ];

  return (
    <div className="size-full bg-[#0A0C10] p-6 overflow-auto">
      <div className="max-w-6xl mx-auto">
        <h2 className="text-2xl mb-6" style={{ fontFamily: 'var(--font-display)' }}>Earnings Dashboard</h2>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
          {stats.map((stat) => (
            <div key={stat.label} className="bg-[#12151C] border border-[#1E2433] rounded-xl p-4">
              <div className="text-sm text-[#94A3B8] mb-2">{stat.label}</div>
              <div className={`text-2xl font-bold ${stat.color}`} style={{ fontFamily: 'var(--font-mono)' }}>
                {dashboardLoading ? '...' : stat.value}
              </div>
            </div>
          ))}
        </div>

        <div className="bg-[#12151C] border border-[#1E2433] rounded-xl p-6 mb-6">
          <h3 className="text-lg mb-4">Today's Trips</h3>
          {dashboardError ? (
            <div className="text-sm text-[#EF4444]">{dashboardError}</div>
          ) : dashboardLoading ? (
            <div className="text-sm text-[#94A3B8]">Loading trips...</div>
          ) : (dashboard?.recentTrips?.length ?? 0) === 0 ? (
            <div className="text-sm text-[#94A3B8]">No completed trips yet today.</div>
          ) : (
            <div className="space-y-3">
              {dashboard.recentTrips.map((trip: any) => (
                <div key={trip.id} className="bg-[#1A1E28] rounded-lg p-4 flex items-center justify-between hover:border-l-4 hover:border-[#3B82F6] transition-all">
                <div className="flex items-center gap-4">
                  <div className="text-sm text-[#94A3B8]" style={{ fontFamily: 'var(--font-mono)' }}>
                    {trip.time}
                  </div>
                  <div>
                    <div className="font-medium">{trip.route}</div>
                    <div className="text-sm text-[#94A3B8] flex items-center gap-1">
                      {trip.rating == null ? (
                        <span>No rating yet</span>
                      ) : (
                        Array.from({ length: Math.max(0, Math.min(5, Math.round(trip.rating))) }).map((_, i) => (
                          <Star key={i} className="w-3 h-3 fill-[#F59E0B] text-[#F59E0B]" />
                        ))
                      )}
                    </div>
                  </div>
                </div>
                <div className="text-xl font-bold text-[#3B82F6]" style={{ fontFamily: 'var(--font-mono)' }}>
                  ${Number(trip.fare ?? 0).toFixed(2)}
                </div>
              </div>
              ))}
            </div>
          )}
        </div>

        <button
          onClick={() => setScreen('home')}
          className="bg-[#3B82F6] hover:bg-[#3B82F6]/90 text-white px-6 py-3 rounded-lg"
        >
          Back to Home
        </button>
      </div>
    </div>
  );
}

function ProfileScreen({ setScreen }: any) {
  // Reuse the shared ProfilePage so drivers see the same account UI as riders.
  return <ProfilePage onBackHome={() => setScreen('home')} />;
}

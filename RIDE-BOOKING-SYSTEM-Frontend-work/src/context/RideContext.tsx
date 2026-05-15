import { createContext, useContext, useState, ReactNode } from 'react';

interface RideContextValue {
  activeRide: unknown;
  setActiveRide: (ride: unknown) => void;
  clearRide: () => void;
}

const RideContext = createContext<RideContextValue | null>(null);

export function RideProvider({ children }: { children: ReactNode }) {
  const [activeRide, setActiveRide] = useState<unknown>(null);
  return (
    <RideContext.Provider value={{ activeRide, setActiveRide, clearRide: () => setActiveRide(null) }}>
      {children}
    </RideContext.Provider>
  );
}

export const useRideContext = () => {
  const ctx = useContext(RideContext);
  if (!ctx) throw new Error('useRideContext must be used inside RideProvider');
  return ctx;
};

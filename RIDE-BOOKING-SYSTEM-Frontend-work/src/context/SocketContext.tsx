import { createContext, useContext, useEffect, useRef, useState, ReactNode } from 'react';
import { createRiderSocket } from '../services/websocket/riderSocket';
import { createDriverSocket } from '../services/websocket/driverSocket';

type SocketContextValue = {
  riderSocket: ReturnType<typeof createRiderSocket> | null;
  driverSocket: ReturnType<typeof createDriverSocket> | null;
};

const SocketContext = createContext<SocketContextValue>({ riderSocket: null, driverSocket: null });

export function SocketProvider({ userId, driverId, children }: { userId?: string; driverId?: string; children: ReactNode }) {
  const riderRef = useRef<ReturnType<typeof createRiderSocket> | null>(null);
  const driverRef = useRef<ReturnType<typeof createDriverSocket> | null>(null);
  const [sockets, setSockets] = useState<SocketContextValue>({ riderSocket: null, driverSocket: null });

  useEffect(() => {
    let riderSocket: ReturnType<typeof createRiderSocket> | null = null;
    let driverSocket: ReturnType<typeof createDriverSocket> | null = null;

    if (userId) {
      riderSocket = createRiderSocket(userId);
      riderSocket.connect();
      riderRef.current = riderSocket;
    }
    if (driverId) {
      driverSocket = createDriverSocket(driverId);
      driverSocket.connect();
      driverRef.current = driverSocket;
    }

    // Trigger re-render so consumers get the real socket instances, not null
    setSockets({ riderSocket, driverSocket });

    return () => {
      riderRef.current?.disconnect();
      driverRef.current?.disconnect();
      riderRef.current = null;
      driverRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [userId, driverId]);

  return (
    <SocketContext.Provider value={sockets}>
      {children}
    </SocketContext.Provider>
  );
}

export const useSocketContext = () => useContext(SocketContext);

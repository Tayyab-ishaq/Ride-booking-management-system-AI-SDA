import { createContext, useContext, useCallback, ReactNode } from 'react';

type ToastType = 'success' | 'error' | 'info' | 'warning';

interface Notification { message: string; type?: ToastType }
interface NotificationContextValue { notify: (n: Notification) => void }

const NotificationContext = createContext<NotificationContextValue>({ notify: () => {} });

// Uses console + can be wired to any toast library (sonner, react-hot-toast, etc.)
export function NotificationProvider({ children }: { children: ReactNode }) {
  const notify = useCallback(({ message, type = 'info' }: Notification) => {
    // Replace with your toast call, e.g. toast[type](message)
    console.log(`[${type.toUpperCase()}] ${message}`);
  }, []);

  return (
    <NotificationContext.Provider value={{ notify }}>
      {children}
    </NotificationContext.Provider>
  );
}

export const useNotification = () => useContext(NotificationContext);

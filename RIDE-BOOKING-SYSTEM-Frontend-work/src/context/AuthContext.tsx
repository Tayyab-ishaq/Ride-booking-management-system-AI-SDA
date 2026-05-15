import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { authApi } from '../api/authApi';
import { driverApi } from '../api/driverApi';
import { rideApi } from '../api/rideApi';
import { tokenStorage } from '../utils/tokenStorage';
import { ROLES, Role } from '../constants/roles';

interface AuthUser { id: string; name: string; email?: string; phone?: string; role: Role }

interface AuthContextValue {
  user: AuthUser | null;
  role: Role | null;
  isAuthenticated: boolean;
  loading: boolean;
  login: (creds: { email?: string; phone?: string; password: string }) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!tokenStorage.hasTokens()) { setLoading(false); return; }
    authApi.me()
      .then(({ data }) => setUser(data))
      .catch(() => tokenStorage.clear())
      .finally(() => setLoading(false));
  }, []);

  const login = async (creds: { email?: string; phone?: string; password: string }) => {
    const { data } = await authApi.login(creds);
    tokenStorage.setTokens(data.access_token, data.refresh_token);
    const me = await authApi.me();
    setUser(me.data);
  };

  const logout = async () => {
    const currentUser = user;

    // attempt to cancel any active rides for the user before clearing tokens
    try {
      const res = await rideApi.history({ page: 1, page_size: 100 });
      const list = (res as any)?.data?.rides ?? [];
      const activeStatuses = ['requested', 'accepted', 'in_progress'];
      const active = list.filter((r: any) => activeStatuses.includes(r.status));
      if (active.length) {
        await Promise.allSettled(active.map((r: any) => rideApi.cancel(r.id)));
      }
    } catch (e) {
      // non-fatal: log and continue logout
      // eslint-disable-next-line no-console
      console.error('Failed to cancel active rides on logout', e);
    }

    try {
      if (currentUser?.role === ROLES.DRIVER) {
        await driverApi.setAvailability(false);
        await driverApi.deleteLocations();
      }
    } catch (e) {
      // non-fatal: log and continue logout
      // eslint-disable-next-line no-console
      console.error('Failed to mark driver offline on logout', e);
    }

    try { await authApi.logout(); } catch {}
    tokenStorage.clear();
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{
      user, role: user?.role ?? null,
      isAuthenticated: !!user, loading, login, logout
    }}>
      {children}
    </AuthContext.Provider>
  );
}

export const useAuthContext = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuthContext must be used inside AuthProvider');
  return ctx;
};

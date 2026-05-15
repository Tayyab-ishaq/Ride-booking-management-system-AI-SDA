import { useState, useCallback } from 'react';
import { authApi } from '../api/authApi';
import { tokenStorage } from '../utils/tokenStorage';

export function useAuth() {
  const [user, setUser] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const login = useCallback(async (credentials: { email?: string; phone?: string; password: string }) => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await authApi.login(credentials);
      tokenStorage.setTokens(data.access_token, data.refresh_token);
      const me = await authApi.me();
      setUser(me.data);
      return me.data;
    } catch (e: unknown) {
      const msg = (e as any)?.response?.data?.detail ?? 'Login failed';
      setError(msg);
      throw e;
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    try { await authApi.logout(); } catch {}
    tokenStorage.clear();
    setUser(null);
  }, []);

  const fetchMe = useCallback(async () => {
    if (!tokenStorage.hasTokens()) return;
    try {
      const { data } = await authApi.me();
      setUser(data);
    } catch {}
  }, []);

  return { user, loading, error, login, logout, fetchMe };
}

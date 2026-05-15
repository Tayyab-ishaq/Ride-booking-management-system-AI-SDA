const ACCESS_KEY = 'uc_access_token';
const REFRESH_KEY = 'uc_refresh_token';
const storage = sessionStorage;

export const tokenStorage = {
  getAccess: () => storage.getItem(ACCESS_KEY),
  getRefresh: () => storage.getItem(REFRESH_KEY),
  setAccess: (token: string) => storage.setItem(ACCESS_KEY, token),
  setRefresh: (token: string) => storage.setItem(REFRESH_KEY, token),
  setTokens: (access: string, refresh: string) => {
    storage.setItem(ACCESS_KEY, access);
    storage.setItem(REFRESH_KEY, refresh);
  },
  clear: () => {
    storage.removeItem(ACCESS_KEY);
    storage.removeItem(REFRESH_KEY);
  },
  hasTokens: () => !!storage.getItem(ACCESS_KEY),
};

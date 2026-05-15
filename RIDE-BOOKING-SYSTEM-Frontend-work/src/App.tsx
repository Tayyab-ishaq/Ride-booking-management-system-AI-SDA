import { useEffect, useState } from 'react';
import { Navigate, Route, Routes } from 'react-router-dom';
import { RiderPortal } from './pages/rider/RiderPortal';
import { DriverPortal } from './pages/driver/DriverPortal';
import { AdminPortal } from './pages/admin/AdminPortal';
import { ProfilePage } from './pages/ProfilePage';
import { LoginPage } from './pages/auth/LoginPage';
import { RegisterPage } from './pages/auth/RegisterPage';
import { useAuthContext } from './context/AuthContext';
import { SocketProvider } from './context/SocketContext';
import { ROLES } from './constants/roles';
import { ROUTES } from './routes/routeConfig';

type Portal = 'rider' | 'driver' | 'admin';

function PortalShell() {
  const { role, user } = useAuthContext();
  const [activePortal, setActivePortal] = useState<Portal>('rider');

  useEffect(() => {
    if (role === ROLES.DRIVER) {
      setActivePortal('driver');
      return;
    }

    if (role === ROLES.ADMIN) {
      setActivePortal('admin');
      return;
    }

    setActivePortal('rider');
  }, [role]);

  if (role === ROLES.DRIVER) {
    // keep the shell on the driver's portal by default, but still render the switcher below
  }

  return (
    <SocketProvider
      userId={user?.id}
      driverId={role === ROLES.DRIVER ? user?.id : undefined}
    >
      <div className="size-full flex flex-col overflow-hidden bg-[#0A0C10]">
        {/* Portal shell chooses portal from authenticated role (no manual switcher) */}

        {/* Active Portal */}
        <div className="flex-1 overflow-hidden">
          {activePortal === 'rider' && <RiderPortal />}
          {activePortal === 'driver' && <DriverPortal />}
          {activePortal === 'admin' && <AdminPortal />}
        </div>
      </div>
    </SocketProvider>
  );
}

function RequireAuth({ children }: { children: JSX.Element }) {
  const { isAuthenticated, loading } = useAuthContext();

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0A0C10] text-white flex items-center justify-center">
        <div className="text-sm text-[#94A3B8]">Loading authentication...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to={ROUTES.LOGIN} replace />;
  }

  return children;
}

function PublicOnly({ children }: { children: JSX.Element }) {
  const { loading } = useAuthContext();

  if (loading) {
    return (
      <div className="min-h-screen bg-[#0A0C10] text-white flex items-center justify-center">
        <div className="text-sm text-[#94A3B8]">Loading authentication...</div>
      </div>
    );
  }

  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to={ROUTES.LOGIN} replace />} />
      <Route
        path={ROUTES.LOGIN}
        element={(
          <PublicOnly>
            <LoginPage />
          </PublicOnly>
        )}
      />
      <Route
        path={ROUTES.REGISTER}
        element={(
          <PublicOnly>
            <RegisterPage />
          </PublicOnly>
        )}
      />
      <Route
        path={ROUTES.APP_HOME}
        element={(
          <RequireAuth>
            <PortalShell />
          </RequireAuth>
        )}
      />
      <Route
        path={ROUTES.DRIVER_HOME}
        element={(
          <RequireAuth>
            <PortalShell />
          </RequireAuth>
        )}
      />
      <Route
        path={ROUTES.PROFILE}
        element={(
          <RequireAuth>
            <ProfilePage />
          </RequireAuth>
        )}
      />
      <Route path="*" element={<Navigate to={ROUTES.LOGIN} replace />} />
    </Routes>
  );
}

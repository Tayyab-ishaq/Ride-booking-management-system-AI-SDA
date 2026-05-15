import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthContext } from '../context/AuthContext';
import { authApi } from '../api/authApi';
import { ROUTES } from '../routes/routeConfig';
import { ArrowLeft, LogOut, User, Mail, Shield, Calendar, Loader } from 'lucide-react';

interface UserProfile {
  id: string;
  full_name: string;
  email: string;
  role: string;
  created_at: string;
  updated_at: string;
}

interface ProfilePageProps {
  onBackHome?: () => void;
}

export function ProfilePage({ onBackHome }: ProfilePageProps = {}) {
  const navigate = useNavigate();
  const { logout, isAuthenticated } = useAuthContext();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [loggingOut, setLoggingOut] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate(ROUTES.LOGIN, { replace: true });
      return;
    }

    fetchProfile();
  }, [isAuthenticated, navigate]);

  const fetchProfile = async () => {
    try {
      setLoading(true);
      setError(null);
      const { data } = await authApi.me();
      setProfile(data);
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'Failed to load profile. Please try again.';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    setLoggingOut(true);
    try {
      await logout();
      navigate(ROUTES.LOGIN, { replace: true });
    } catch (err: unknown) {
      const message =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
        'Logout failed. Please try again.';
      setError(message);
      setLoggingOut(false);
    }
  };

  const handleBackHome = () => {
    if (onBackHome) {
      onBackHome();
      return;
    }
    navigate(ROUTES.APP_HOME, { replace: true });
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#0A0C10]">
        <div className="flex flex-col items-center gap-4">
          <Loader className="h-8 w-8 animate-spin text-[#3B82F6]" />
          <p className="text-[#94A3B8]">Loading your profile...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-[#0A0C10] to-[#0F131A] py-12 px-4">
      <div className="mx-auto max-w-2xl">
        {error && (
          <div className="mb-6 rounded-2xl border border-red-500/20 bg-red-500/10 px-6 py-4 text-sm text-red-200">
            {error}
          </div>
        )}

        <div className="rounded-3xl border border-white/10 bg-[#0F131A]/50 backdrop-blur-xl p-8 shadow-2xl">
          {/* Header */}
          <div className="mb-8 flex items-start justify-between border-b border-white/10 pb-8">
            <div>
              <div className="mb-2 flex items-center gap-2">
                <div className="rounded-full bg-[#3B82F6]/20 p-2">
                  <User className="h-5 w-5 text-[#3B82F6]" />
                </div>
                <h1 className="text-3xl font-bold text-white">My Profile</h1>
              </div>
              <p className="text-[#94A3B8]">Manage your account information</p>
            </div>
            <div className="flex items-center gap-3">
              <button
                onClick={handleBackHome}
                className="flex items-center gap-2 rounded-xl bg-white/5 px-4 py-2 text-sm font-medium text-white transition hover:bg-white/10"
              >
                <ArrowLeft className="h-4 w-4" />
                Back to Home
              </button>
              <button
                onClick={handleLogout}
                disabled={loggingOut}
                className="flex items-center gap-2 rounded-xl bg-red-500/20 px-4 py-2 text-sm font-medium text-red-200 transition hover:bg-red-500/30 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <LogOut className="h-4 w-4" />
                {loggingOut ? 'Logging out...' : 'Logout'}
              </button>
            </div>
          </div>

          {/* Profile Content */}
          {profile ? (
            <div className="space-y-6">
              {/* Full Name */}
              <div className="rounded-xl bg-white/5 p-4 backdrop-blur">
                <p className="mb-1 text-xs uppercase tracking-widest text-[#94A3B8]">Full Name</p>
                <p className="text-lg font-semibold text-white">{profile.full_name}</p>
              </div>

              {/* Email */}
              <div className="rounded-xl bg-white/5 p-4 backdrop-blur">
                <div className="mb-1 flex items-center gap-2">
                  <Mail className="h-4 w-4 text-[#3B82F6]" />
                  <p className="text-xs uppercase tracking-widest text-[#94A3B8]">Email Address</p>
                </div>
                <p className="text-lg font-semibold text-white">{profile.email}</p>
              </div>

              {/* Role */}
              <div className="rounded-xl bg-white/5 p-4 backdrop-blur">
                <div className="mb-1 flex items-center gap-2">
                  <Shield className="h-4 w-4 text-[#10B981]" />
                  <p className="text-xs uppercase tracking-widest text-[#94A3B8]">Role</p>
                </div>
                <div className="flex items-center gap-2">
                  <span className="inline-block rounded-full bg-[#10B981]/20 px-3 py-1 text-sm font-medium capitalize text-[#10B981]">
                    {profile.role}
                  </span>
                </div>
              </div>

              {/* Account Created */}
              <div className="grid grid-cols-2 gap-4">
                <div className="rounded-xl bg-white/5 p-4 backdrop-blur">
                  <div className="mb-1 flex items-center gap-2">
                    <Calendar className="h-4 w-4 text-[#F59E0B]" />
                    <p className="text-xs uppercase tracking-widest text-[#94A3B8]">Joined</p>
                  </div>
                  <p className="text-sm font-semibold text-white">
                    {new Date(profile.created_at).toLocaleDateString('en-US', {
                      year: 'numeric',
                      month: 'short',
                      day: 'numeric',
                    })}
                  </p>
                </div>

                <div className="rounded-xl bg-white/5 p-4 backdrop-blur">
                  <div className="mb-1 flex items-center gap-2">
                    <Calendar className="h-4 w-4 text-[#8B5CF6]" />
                    <p className="text-xs uppercase tracking-widest text-[#94A3B8]">Last Updated</p>
                  </div>
                  <p className="text-sm font-semibold text-white">
                    {new Date(profile.updated_at).toLocaleDateString('en-US', {
                      year: 'numeric',
                      month: 'short',
                      day: 'numeric',
                    })}
                  </p>
                </div>
              </div>

              {/* Action Buttons */}
              {/* <div className="mt-8 flex gap-4 border-t border-white/10 pt-8">
                <button
                  onClick={() => window.location.reload()}
                  className="flex-1 rounded-xl bg-[#3B82F6]/20 px-4 py-3 font-medium text-[#3B82F6] transition hover:bg-[#3B82F6]/30"
                >
                  Refresh
                </button>
                <button
                  onClick={handleLogout}
                  disabled={loggingOut}
                  className="flex-1 rounded-xl bg-red-500/20 px-4 py-3 font-medium text-red-200 transition hover:bg-red-500/30 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {loggingOut ? 'Logging out...' : 'Logout'}
                </button>
              </div> */}
            </div>
          ) : (
            <div className="text-center">
              <p className="text-[#94A3B8]">No profile data available</p>
              <button
                onClick={fetchProfile}
                className="mt-4 rounded-xl bg-[#3B82F6] px-4 py-2 font-medium text-white transition hover:brightness-110"
              >
                Try Again
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default ProfilePage;

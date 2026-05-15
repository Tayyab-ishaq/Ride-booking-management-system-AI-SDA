import { useEffect, useState } from 'react';
import {
  LayoutDashboard,
  Car,
  Users,
  CreditCard,
  BarChart3,
  Shield,
  Settings,
  Search,
  Bell,
  User,
  TrendingUp,
  Activity,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Eye,
  Ban,
  Send,
  Download,
  MapPin,
  Clock,
  DollarSign,
  Zap,
  Star,
} from 'lucide-react';
import { MapView } from '../../components/map/RideMap';
import { adminApi } from '../../api/adminApi';

type AdminScreen = 'dashboard' | 'rides' | 'users' | 'analytics' | 'fraud';

export function AdminPortal() {
  const [screen, setScreen] = useState<AdminScreen>('dashboard');
  const [sidebarExpanded, setSidebarExpanded] = useState(true);
  const [dashboard, setDashboard] = useState<any>(null);
  const [rides, setRides] = useState<any[]>([]);
  const [users, setUsers] = useState<any[]>([]);

  useEffect(() => {
    const load = async () => {
      try {
        const [dashboardRes, ridesRes, usersRes] = await Promise.all([
          adminApi.dashboard(),
          adminApi.rides(50),
          adminApi.users(50),
        ]);
        setDashboard(dashboardRes.data);
        setRides(ridesRes.data?.rides ?? []);
        setUsers(usersRes.data?.users ?? []);
      } catch (error) {
        console.error('Admin data load failed', error);
      }
    };
    load();
  }, []);

  return (
    <div className="size-full flex overflow-hidden">
      <Sidebar
        expanded={sidebarExpanded}
        setSidebarExpanded={setSidebarExpanded}
        screen={screen}
        setScreen={setScreen}
      />

      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />

        <div className="flex-1 overflow-auto bg-[#0A0C10] p-6">
          {screen === 'dashboard' && <DashboardScreen dashboard={dashboard} />}
          {screen === 'rides' && <RidesScreen rides={rides} />}
          {screen === 'users' && <UsersScreen users={users} />}
          {screen === 'analytics' && <AnalyticsScreen />}
          {screen === 'fraud' && <FraudScreen />}
        </div>
      </div>
    </div>
  );
}

function Sidebar({ expanded, setSidebarExpanded, screen, setScreen }: any) {
  const menuItems = [
    { id: 'dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { id: 'rides', icon: Car, label: 'Rides' },
    { id: 'users', icon: Users, label: 'Users' },
    { id: 'analytics', icon: BarChart3, label: 'Analytics' },
    { id: 'fraud', icon: Shield, label: 'Fraud Monitor' },
  ];

  return (
    <div
      className={`bg-[#12151C] border-r border-[#1E2433] transition-all duration-300 ${
        expanded ? 'w-64' : 'w-20'
      }`}
    >
      <div className="p-4">
        <button
          onClick={() => setSidebarExpanded(!expanded)}
          className="w-full flex items-center gap-3 p-3 hover:bg-[#1A1E28] rounded-lg transition-all"
        >
          <Shield className="w-6 h-6 text-[#8B5CF6]" />
          {expanded && (
            <span className="font-bold" style={{ fontFamily: 'var(--font-display)' }}>
              Admin
            </span>
          )}
        </button>
      </div>

      <nav className="px-3 space-y-1">
        {menuItems.map((item) => (
          <button
            key={item.id}
            onClick={() => setScreen(item.id)}
            className={`w-full flex items-center gap-3 p-3 rounded-lg transition-all ${
              screen === item.id
                ? 'bg-[#8B5CF6] text-white shadow-lg shadow-[#8B5CF6]/30'
                : 'text-[#94A3B8] hover:bg-[#1A1E28] hover:text-[#F1F5F9]'
            }`}
          >
            <item.icon className="w-5 h-5" />
            {expanded && <span className="text-sm">{item.label}</span>}
          </button>
        ))}
      </nav>
    </div>
  );
}

function Header() {
  return (
    <header className="h-16 bg-[#12151C] border-b border-[#1E2433] flex items-center justify-between px-6">
      <div className="flex-1 max-w-xl">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[#94A3B8]" />
          <input
            type="text"
            placeholder="Search rides, users, transactions..."
            className="w-full bg-[#1A1E28] border border-[#1E2433] rounded-lg pl-10 pr-4 py-2 text-sm text-[#F1F5F9] placeholder:text-[#94A3B8] focus:outline-none focus:ring-2 focus:ring-[#8B5CF6]"
          />
        </div>
      </div>

      <div className="flex items-center gap-4">
        <button className="relative p-2 hover:bg-[#1A1E28] rounded-lg transition-colors">
          <Bell className="w-5 h-5 text-[#94A3B8]" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-[#EF4444] rounded-full"></span>
        </button>
        <div className="flex items-center gap-3 pl-4 border-l border-[#1E2433]">
          <div className="w-8 h-8 bg-gradient-to-br from-[#8B5CF6] to-[#6D28D9] rounded-full flex items-center justify-center text-sm font-bold">
            AD
          </div>
          <div className="text-sm">
            <div className="font-medium">Admin User</div>
            <div className="text-xs text-[#94A3B8]">Super Admin</div>
          </div>
        </div>
      </div>
    </header>
  );
}

function DashboardScreen({ dashboard }: { dashboard: any }) {
  const kpis = [
    { label: 'Active Rides', value: String(dashboard?.active_rides ?? 0), icon: Activity, color: 'text-[#10B981]', live: true },
    { label: 'Drivers Online', value: String(dashboard?.total_drivers ?? 0), icon: Car, color: 'text-[#3B82F6]' },
    { label: 'Total Revenue', value: `$${dashboard?.total_revenue ?? 0}`, icon: DollarSign, color: 'text-[#F5A623]' },
    { label: 'Total Users', value: String(dashboard?.total_users ?? 0), icon: Users, color: 'text-[#8B5CF6]' },
    { label: 'Avg. Wait Time', value: '2.3 min', icon: Clock, color: 'text-[#F59E0B]' },
    { label: 'Failed Payments', value: String(dashboard?.failed_payments ?? 0), icon: AlertTriangle, color: 'text-[#EF4444]' },
  ];

  const activities = [
    { time: '2s ago', text: 'Ride #4821 completed — $8.20', type: 'success' },
    { time: '14s ago', text: 'New driver signup — Fahad K.', type: 'info' },
    { time: '1m ago', text: '⚠️ Suspicious payment flagged — Ride #4817', type: 'warning' },
    { time: '2m ago', text: 'Surge pricing activated — Clifton zone', type: 'surge' },
    { time: '3m ago', text: 'Ride #4820 completed — $12.50', type: 'success' },
    { time: '4m ago', text: 'New rider signup — Maria S.', type: 'info' },
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold" style={{ fontFamily: 'var(--font-display)' }}>
        Command Center
      </h1>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
        {kpis.map((kpi) => (
          <div key={kpi.label} className="bg-[#12151C] border border-[#1E2433] rounded-xl p-4 hover:border-[#8B5CF6]/50 transition-all">
            <div className="flex items-start justify-between mb-3">
              <kpi.icon className={`w-5 h-5 ${kpi.color}`} />
              {kpi.live && (
                <div className="flex items-center gap-1 text-xs text-[#10B981]">
                  <div className="w-2 h-2 bg-[#10B981] rounded-full animate-pulse"></div>
                  LIVE
                </div>
              )}
            </div>
            <div className={`text-2xl font-bold ${kpi.color} mb-1`} style={{ fontFamily: 'var(--font-mono)' }}>
              {kpi.value}
            </div>
            <div className="text-xs text-[#94A3B8]">{kpi.label}</div>
          </div>
        ))}
      </div>

      {/* Main Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Live Map */}
        <div className="lg:col-span-2 bg-[#12151C] border border-[#1E2433] rounded-xl overflow-hidden">
          <div className="p-4 border-b border-[#1E2433]">
            <h3 className="font-medium">Live Ride Map</h3>
          </div>
          <div className="h-96 relative">
            <MapView />
          </div>
        </div>

        {/* Activity Feed */}
        <div className="bg-[#12151C] border border-[#1E2433] rounded-xl overflow-hidden">
          <div className="p-4 border-b border-[#1E2433] flex items-center justify-between">
            <h3 className="font-medium">Recent Activity</h3>
            <button className="text-sm text-[#8B5CF6]">View All</button>
          </div>
          <div className="p-4 space-y-3 max-h-96 overflow-y-auto">
            {activities.map((activity, i) => (
              <div key={i} className="flex gap-3 text-sm">
                <div
                  className={`w-2 h-2 rounded-full mt-2 flex-shrink-0 ${
                    activity.type === 'success'
                      ? 'bg-[#10B981]'
                      : activity.type === 'warning'
                      ? 'bg-[#F59E0B]'
                      : activity.type === 'surge'
                      ? 'bg-[#F5A623]'
                      : 'bg-[#3B82F6]'
                  }`}
                ></div>
                <div className="flex-1">
                  <div className="text-[#F1F5F9]">{activity.text}</div>
                  <div className="text-xs text-[#94A3B8]">{activity.time}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-[#12151C] border border-[#1E2433] rounded-xl p-6">
          <h3 className="font-medium mb-4">Revenue (Last 30 Days)</h3>
          <div className="h-48 flex items-end gap-2">
            {Array.from({ length: 30 }).map((_, i) => (
              <div key={i} className="flex-1 bg-[#8B5CF6] rounded-t opacity-70 hover:opacity-100 transition-all" style={{ height: `${Math.random() * 100}%` }}></div>
            ))}
          </div>
        </div>

        <div className="bg-[#12151C] border border-[#1E2433] rounded-xl p-6">
          <h3 className="font-medium mb-4">Rides per Hour (Today)</h3>
          <div className="h-48 flex items-end gap-2">
            {Array.from({ length: 24 }).map((_, i) => (
              <div key={i} className="flex-1 bg-[#3B82F6] rounded-t opacity-70 hover:opacity-100 transition-all" style={{ height: `${Math.random() * 100}%` }}></div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function RidesScreen({ rides }: { rides: any[] }) {
  const fallbackRides = [
    { id: '#4821', rider: 'Sara M.', driver: 'Ahmad K.', pickup: 'Downtown', dropoff: 'Airport', status: 'Completed', fare: '$18.50', date: '2026-04-22 14:32' },
    { id: '#4820', rider: 'John D.', driver: 'Fahad K.', pickup: 'Mall', dropoff: 'Office', status: 'Completed', fare: '$12.50', date: '2026-04-22 14:28' },
    { id: '#4819', rider: 'Lisa A.', driver: 'Maria S.', pickup: 'Home', dropoff: 'University', status: 'Active', fare: '$8.20', date: '2026-04-22 14:25' },
    { id: '#4818', rider: 'Mike R.', driver: 'Omar H.', pickup: 'Station', dropoff: 'Hotel', status: 'Active', fare: '$15.30', date: '2026-04-22 14:20' },
    { id: '#4817', rider: 'Anna K.', driver: 'Ali M.', pickup: 'Airport', dropoff: 'Downtown', status: 'Disputed', fare: '$22.40', date: '2026-04-22 14:15' },
  ];
  const rows = rides.length
    ? rides.map((ride) => ({
        id: ride.id,
        rider: ride.rider_id,
        driver: ride.driver_id ?? '-',
        pickup: ride.origin,
        dropoff: ride.destination,
        status: String(ride.status ?? '').replace('_', ' '),
        fare: ride.fare ? `$${ride.fare}` : 'N/A',
      }))
    : fallbackRides;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold" style={{ fontFamily: 'var(--font-display)' }}>
          Rides Management
        </h1>
      </div>

      <div className="flex gap-2">
        {['All', 'Active', 'Completed', 'Cancelled', 'Disputed'].map((status) => (
          <button
            key={status}
            className={`px-4 py-2 rounded-lg text-sm transition-all ${
              status === 'All'
                ? 'bg-[#8B5CF6] text-white'
                : 'bg-[#1A1E28] text-[#94A3B8] hover:bg-[#1E2433]'
            }`}
          >
            {status}
          </button>
        ))}
      </div>

      <div className="bg-[#12151C] border border-[#1E2433] rounded-xl overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-[#1A1E28] border-b border-[#1E2433]">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium text-[#94A3B8]">Ride ID</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-[#94A3B8]">Rider</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-[#94A3B8]">Driver</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-[#94A3B8]">Route</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-[#94A3B8]">Status</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-[#94A3B8]">Fare</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-[#94A3B8]">Actions</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((ride, i) => (
                <tr
                  key={ride.id}
                  className={`border-b border-[#1E2433] hover:bg-[#1A1E28] hover:border-l-4 hover:border-l-[#8B5CF6] transition-all ${
                    i % 2 === 0 ? 'bg-[#12151C]' : 'bg-[#0A0C10]'
                  }`}
                >
                  <td className="px-4 py-3">
                    <span className="font-mono text-sm">{ride.id}</span>
                  </td>
                  <td className="px-4 py-3 text-sm">{ride.rider}</td>
                  <td className="px-4 py-3 text-sm">{ride.driver}</td>
                  <td className="px-4 py-3 text-sm text-[#94A3B8]">
                    {ride.pickup} → {ride.dropoff}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex px-2 py-1 rounded text-xs ${
                        String(ride.status).toLowerCase() === 'completed'
                          ? 'bg-[#10B981]/20 text-[#10B981]'
                          : ['requested', 'offered', 'accepted', 'in progress', 'in_progress', 'active'].includes(String(ride.status).toLowerCase())
                          ? 'bg-[#3B82F6]/20 text-[#3B82F6]'
                          : 'bg-[#EF4444]/20 text-[#EF4444]'
                      }`}
                    >
                      {ride.status}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className="font-mono text-[#F5A623]">{ride.fare}</span>
                  </td>
                  <td className="px-4 py-3">
                    <button className="text-[#8B5CF6] hover:underline text-sm">View</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="px-4 py-3 bg-[#1A1E28] border-t border-[#1E2433] flex items-center justify-between text-sm">
          <span className="text-[#94A3B8]">Showing 1–5 of 1,482 results</span>
          <div className="flex gap-2">
            <button className="px-3 py-1 bg-[#12151C] border border-[#1E2433] rounded hover:bg-[#1E2433]">Previous</button>
            <button className="px-3 py-1 bg-[#8B5CF6] text-white rounded">1</button>
            <button className="px-3 py-1 bg-[#12151C] border border-[#1E2433] rounded hover:bg-[#1E2433]">2</button>
            <button className="px-3 py-1 bg-[#12151C] border border-[#1E2433] rounded hover:bg-[#1E2433]">3</button>
            <button className="px-3 py-1 bg-[#12151C] border border-[#1E2433] rounded hover:bg-[#1E2433]">Next</button>
          </div>
        </div>
      </div>
    </div>
  );
}

function UsersScreen({ users }: { users: any[] }) {
  const [activeTab, setActiveTab] = useState<'riders' | 'drivers'>('riders');

  const fallbackUsers = [
    { name: 'Sara M.', email: 'sara.m@email.com', phone: '+1234567890', joined: '2026-01-15', trips: 47, status: 'Active' },
    { name: 'John D.', email: 'john.d@email.com', phone: '+1234567891', joined: '2026-02-20', trips: 32, status: 'Active' },
    { name: 'Lisa A.', email: 'lisa.a@email.com', phone: '+1234567892', joined: '2026-03-10', trips: 18, status: 'Active' },
    { name: 'Mike R.', email: 'mike.r@email.com', phone: '+1234567893', joined: '2026-04-01', trips: 5, status: 'Pending' },
  ];
  const rows = users.length
    ? users
        .filter((user) => (activeTab === 'drivers' ? user.role === 'driver' : user.role === 'rider'))
        .map((user) => ({
          name: user.full_name,
          email: user.email,
          phone: '-',
          joined: user.created_at,
          trips: '-',
          status: 'Active',
        }))
    : fallbackUsers;

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold" style={{ fontFamily: 'var(--font-display)' }}>
        User Management
      </h1>

      <div className="flex gap-2">
        <button
          onClick={() => setActiveTab('riders')}
          className={`px-6 py-3 rounded-lg transition-all ${
            activeTab === 'riders' ? 'bg-[#8B5CF6] text-white' : 'bg-[#1A1E28] text-[#94A3B8]'
          }`}
        >
          Riders
        </button>
        <button
          onClick={() => setActiveTab('drivers')}
          className={`px-6 py-3 rounded-lg transition-all ${
            activeTab === 'drivers' ? 'bg-[#8B5CF6] text-white' : 'bg-[#1A1E28] text-[#94A3B8]'
          }`}
        >
          Drivers
        </button>
      </div>

      <div className="bg-[#12151C] border border-[#1E2433] rounded-xl overflow-hidden">
        <table className="w-full">
          <thead className="bg-[#1A1E28] border-b border-[#1E2433]">
            <tr>
              <th className="px-4 py-3 text-left text-sm font-medium text-[#94A3B8]">Name</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-[#94A3B8]">Email</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-[#94A3B8]">Phone</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-[#94A3B8]">Joined</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-[#94A3B8]">Total Rides</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-[#94A3B8]">Status</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-[#94A3B8]">Actions</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((user, i) => (
              <tr
                key={user.email}
                className={`border-b border-[#1E2433] hover:bg-[#1A1E28] transition-all ${
                  i % 2 === 0 ? 'bg-[#12151C]' : 'bg-[#0A0C10]'
                }`}
              >
                <td className="px-4 py-3">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-gradient-to-br from-[#8B5CF6] to-[#6D28D9] rounded-full flex items-center justify-center text-xs font-bold">
                      {user.name.split(' ').map(n => n[0]).join('')}
                    </div>
                    <span className="font-medium">{user.name}</span>
                  </div>
                </td>
                <td className="px-4 py-3 text-sm text-[#94A3B8]">{user.email}</td>
                <td className="px-4 py-3 text-sm text-[#94A3B8]" style={{ fontFamily: 'var(--font-mono)' }}>{user.phone}</td>
                <td className="px-4 py-3 text-sm text-[#94A3B8]">{user.joined}</td>
                <td className="px-4 py-3 text-sm" style={{ fontFamily: 'var(--font-mono)' }}>{user.trips}</td>
                <td className="px-4 py-3">
                  <span
                    className={`inline-flex px-2 py-1 rounded text-xs ${
                      user.status === 'Active'
                        ? 'bg-[#10B981]/20 text-[#10B981]'
                        : 'bg-[#F59E0B]/20 text-[#F59E0B]'
                    }`}
                  >
                    {user.status}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <div className="flex gap-2">
                    <button className="text-[#8B5CF6] hover:underline text-sm">View</button>
                    <button className="text-[#EF4444] hover:underline text-sm">Suspend</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function AnalyticsScreen() {
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold" style={{ fontFamily: 'var(--font-display)' }}>
        Analytics Dashboard
      </h1>

      <div className="flex gap-2">
        {['7D', '30D', '90D', 'Custom'].map((period) => (
          <button
            key={period}
            className={`px-4 py-2 rounded-lg text-sm transition-all ${
              period === '30D'
                ? 'bg-[#8B5CF6] text-white'
                : 'bg-[#1A1E28] text-[#94A3B8] hover:bg-[#1E2433]'
            }`}
          >
            {period}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {[
          { title: 'Revenue Trend', color: 'bg-[#8B5CF6]' },
          { title: 'Rides Volume', color: 'bg-[#3B82F6]' },
          { title: 'Driver Supply vs Rider Demand', color: 'bg-[#F5A623]' },
          { title: 'Geographic Heatmap', color: 'bg-[#10B981]' },
        ].map((chart) => (
          <div key={chart.title} className="bg-[#12151C] border border-[#1E2433] rounded-xl p-6">
            <h3 className="font-medium mb-4">{chart.title}</h3>
            <div className="h-64 flex items-end gap-2">
              {Array.from({ length: 30 }).map((_, i) => (
                <div
                  key={i}
                  className={`flex-1 ${chart.color} rounded-t opacity-70 hover:opacity-100 transition-all`}
                  style={{ height: `${Math.random() * 100}%` }}
                ></div>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="bg-[#12151C] border border-[#1E2433] rounded-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-medium">n8n Pipeline Status</h3>
          <span className="flex items-center gap-2 text-sm text-[#10B981]">
            <div className="w-2 h-2 bg-[#10B981] rounded-full animate-pulse"></div>
            Healthy
          </span>
        </div>
        <div className="grid grid-cols-3 gap-4">
          {[
            { label: 'Last Run', value: '2 min ago' },
            { label: 'Success Rate', value: '99.8%' },
            { label: 'Recent Triggers', value: '1,247' },
          ].map((stat) => (
            <div key={stat.label} className="bg-[#1A1E28] rounded-lg p-3">
              <div className="text-sm text-[#94A3B8] mb-1">{stat.label}</div>
              <div className="text-lg font-bold text-[#3B82F6]" style={{ fontFamily: 'var(--font-mono)' }}>
                {stat.value}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function FraudScreen() {
  const alerts = [
    { id: 1, severity: 'HIGH', type: 'Multiple payment failures', user: 'Mike R. (#2341)', triggered: '5 min ago' },
    { id: 2, severity: 'MEDIUM', type: 'Unusual ride pattern', user: 'Anna K. (#1892)', triggered: '12 min ago' },
    { id: 3, severity: 'LOW', type: 'Promo code abuse', user: 'Tom S. (#3421)', triggered: '28 min ago' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold flex items-center gap-3" style={{ fontFamily: 'var(--font-display)' }}>
          Fraud Monitor
          <span className="px-3 py-1 bg-[#EF4444] text-white text-sm rounded-full">{alerts.length}</span>
        </h1>
      </div>

      <div className="space-y-4">
        {alerts.map((alert) => (
          <div
            key={alert.id}
            className={`bg-[#12151C] border-2 rounded-xl p-6 ${
              alert.severity === 'HIGH'
                ? 'border-[#EF4444]'
                : alert.severity === 'MEDIUM'
                ? 'border-[#F59E0B]'
                : 'border-[#F5A623]'
            }`}
          >
            <div className="flex items-start justify-between mb-4">
              <div className="flex items-center gap-3">
                <span
                  className={`px-3 py-1 rounded text-xs font-bold ${
                    alert.severity === 'HIGH'
                      ? 'bg-[#EF4444] text-white'
                      : alert.severity === 'MEDIUM'
                      ? 'bg-[#F59E0B] text-white'
                      : 'bg-[#F5A623] text-[#0A0C10]'
                  }`}
                >
                  {alert.severity}
                </span>
                <h3 className="text-lg font-medium">{alert.type}</h3>
              </div>
              <span className="text-sm text-[#94A3B8]">{alert.triggered}</span>
            </div>

            <div className="mb-4">
              <div className="text-sm text-[#94A3B8] mb-1">Flagged User</div>
              <div className="font-medium">{alert.user}</div>
            </div>

            <div className="flex gap-3">
              <button className="flex items-center gap-2 px-4 py-2 bg-[#8B5CF6] hover:bg-[#7C3AED] text-white rounded-lg transition-all">
                <Eye className="w-4 h-4" />
                Investigate
              </button>
              <button className="flex items-center gap-2 px-4 py-2 bg-[#1A1E28] hover:bg-[#1E2433] border border-[#1E2433] rounded-lg transition-all">
                <Ban className="w-4 h-4" />
                Suspend User
              </button>
              <button className="flex items-center gap-2 px-4 py-2 bg-[#1A1E28] hover:bg-[#1E2433] border border-[#1E2433] rounded-lg transition-all">
                <XCircle className="w-4 h-4" />
                Dismiss
              </button>
            </div>
          </div>
        ))}
      </div>

      <div className="bg-[#12151C] border border-[#1E2433] rounded-xl p-6">
        <h3 className="font-medium mb-4">Fraud Trend (Last 30 Days)</h3>
        <div className="h-48 flex items-end gap-2">
          {Array.from({ length: 30 }).map((_, i) => (
            <div
              key={i}
              className="flex-1 bg-[#EF4444] rounded-t opacity-70 hover:opacity-100 transition-all"
              style={{ height: `${Math.random() * 60}%` }}
            ></div>
          ))}
        </div>
      </div>

      <div className="bg-[#12151C] border border-[#1E2433] rounded-xl p-6">
        <h3 className="font-medium mb-4">Detection Rules</h3>
        <div className="space-y-3">
          {[
            'Multiple payment failures (3+ in 24h)',
            'GPS spoofing detection',
            'Promo code abuse pattern',
            'Unusual ride frequency',
          ].map((rule, i) => (
            <div key={i} className="flex items-center justify-between bg-[#1A1E28] rounded-lg p-3">
              <span className="text-sm">{rule}</span>
              <button className="w-12 h-6 bg-[#10B981] rounded-full relative">
                <div className="w-5 h-5 bg-white rounded-full absolute right-0.5 top-0.5 shadow"></div>
              </button>
            </div>
          ))}
        </div>
        <p className="text-xs text-[#94A3B8] mt-4">
          Rules feed from n8n automation workflows — FastAPI → n8n → AI anomaly detection → flag created in DB
        </p>
      </div>
    </div>
  );
}

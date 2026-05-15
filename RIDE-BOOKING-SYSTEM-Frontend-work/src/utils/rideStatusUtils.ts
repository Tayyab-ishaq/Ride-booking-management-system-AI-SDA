import { RIDE_STATUS, RideStatus } from '../constants/rideStatuses';

const STATUS_CONFIG: Record<string, { label: string; color: string; icon: string }> = {
  [RIDE_STATUS.PENDING]:        { label: 'Pending',          color: '#f59e0b', icon: '⏳' },
  [RIDE_STATUS.MATCHING]:       { label: 'Finding Driver',   color: '#3b82f6', icon: '🔍' },
  [RIDE_STATUS.ACCEPTED]:       { label: 'Driver Assigned',  color: '#8b5cf6', icon: '✅' },
  [RIDE_STATUS.DRIVER_ARRIVED]: { label: 'Driver Arrived',   color: '#06b6d4', icon: '📍' },
  [RIDE_STATUS.IN_PROGRESS]:    { label: 'On the Way',       color: '#10b981', icon: '🚗' },
  [RIDE_STATUS.COMPLETED]:      { label: 'Completed',        color: '#1d9e75', icon: '🏁' },
  [RIDE_STATUS.CANCELLED]:      { label: 'Cancelled',        color: '#ef4444', icon: '❌' },
};

export const getRideStatusConfig = (status: string) =>
  STATUS_CONFIG[status] ?? { label: status, color: '#6b7280', icon: '❓' };

export const getRideStatusLabel = (status: string) => getRideStatusConfig(status).label;
export const getRideStatusColor = (status: string) => getRideStatusConfig(status).color;
export const getRideStatusIcon  = (status: string) => getRideStatusConfig(status).icon;

export const isRideActive = (status: string) =>
  [RIDE_STATUS.ACCEPTED, RIDE_STATUS.DRIVER_ARRIVED, RIDE_STATUS.IN_PROGRESS].includes(status as RideStatus);

export const isRideFinal = (status: string) =>
  [RIDE_STATUS.COMPLETED, RIDE_STATUS.CANCELLED].includes(status as RideStatus);

export const RIDE_STATUS = {
  PENDING: 'pending',
  MATCHING: 'matching',
  ACCEPTED: 'accepted',
  DRIVER_ARRIVED: 'driver_arrived',
  IN_PROGRESS: 'in_progress',
  COMPLETED: 'completed',
  CANCELLED: 'cancelled',
} as const;

export type RideStatus = typeof RIDE_STATUS[keyof typeof RIDE_STATUS];

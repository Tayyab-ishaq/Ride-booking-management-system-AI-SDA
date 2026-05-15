export const ROLES = {
  RIDER: 'rider',
  DRIVER: 'driver',
  ADMIN: 'admin',
} as const;

export type Role = typeof ROLES[keyof typeof ROLES];

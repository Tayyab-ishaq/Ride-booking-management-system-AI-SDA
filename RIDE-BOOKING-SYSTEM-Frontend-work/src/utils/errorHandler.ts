import { AxiosError } from 'axios';

export interface ApiError {
  message: string;
  status?: number;
  detail?: string;
}

// Normalises Axios errors into a consistent shape for toast messages
export const normalizeError = (error: unknown): ApiError => {
  if (error instanceof Error && 'response' in error) {
    const axiosError = error as AxiosError<{ detail?: string; message?: string }>;
    const status = axiosError.response?.status;
    const data = axiosError.response?.data;
    const message = data?.detail ?? data?.message ?? axiosError.message ?? 'Something went wrong';
    return { message, status, detail: data?.detail };
  }
  if (error instanceof Error) return { message: error.message };
  return { message: 'An unexpected error occurred' };
};

export const getErrorMessage = (error: unknown): string => normalizeError(error).message;

import { useState, useCallback } from 'react';
import { paymentApi } from '../api/paymentApi';

export function usePayment() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const initiate = useCallback(async (ride_id: string, method_id: string, amount: number) => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await paymentApi.initiate({ ride_id, payment_method: method_id, amount });
      return data;
    } catch (e: any) {
      setError(e?.response?.data?.detail ?? 'Payment initiation failed');
      throw e;
    } finally {
      setLoading(false);
    }
  }, []);

  const confirm = useCallback(async (payment_id: string) => {
    const { data } = await paymentApi.confirm(payment_id);
    return data;
  }, []);

  return { loading, error, initiate, confirm };
}

import { n8nApi } from '../../api/n8nApi';

// Polls /integrations/status for the Admin dashboard WorkflowStatus widget
export class WorkflowMonitor {
  private intervalId: ReturnType<typeof setInterval> | null = null;

  start(onUpdate: (status: unknown) => void, intervalMs = 30000) {
    const poll = async () => {
      try {
        const { data } = await n8nApi.status();
        onUpdate(data);
      } catch {
        console.warn('[WorkflowMonitor] Failed to fetch status');
      }
    };
    poll();
    this.intervalId = setInterval(poll, intervalMs);
  }

  stop() {
    if (this.intervalId) clearInterval(this.intervalId);
    this.intervalId = null;
  }
}

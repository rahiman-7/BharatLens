import { apiClient } from './client';

export interface ReadingEventPayload {
  article_id: number;
  event_type: 'view' | 'read';
  dwell_time_seconds?: number;
}

export interface ReadingEventResponse {
  id: number;
  user_id: number;
  article_id: number;
  event_type: string;
  dwell_time_seconds: number;
  created_at: string;
}

export async function recordReadingEventApi(
  payload: ReadingEventPayload
): Promise<ReadingEventResponse | null> {
  // Safe execution: if user is not authenticated or request fails, fail silently
  const token = typeof window !== 'undefined' ? localStorage.getItem('bharatlens_token') : null;
  if (!token) {
    return null;
  }
  try {
    return await apiClient<ReadingEventResponse>('/reading-events', {
      method: 'POST',
      body: JSON.stringify({
        article_id: payload.article_id,
        event_type: payload.event_type,
        dwell_time_seconds: payload.dwell_time_seconds || 0,
      }),
    });
  } catch {
    // Non-blocking analytics
    return null;
  }
}

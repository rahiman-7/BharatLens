import { useEffect, useRef } from 'react';
import { recordReadingEventApi } from '../api/readingEventsApi';
import { useAuth } from '../auth/AuthContext';

export function useReadingTracker(articleId?: number) {
  const { isAuthenticated } = useAuth();
  const startTimeRef = useRef<number | null>(null);
  const hasTrackedViewRef = useRef<boolean>(false);

  useEffect(() => {
    if (!articleId || !isAuthenticated) {
      return;
    }

    // 1. Track initial view event
    if (!hasTrackedViewRef.current) {
      recordReadingEventApi({
        article_id: articleId,
        event_type: 'view',
        dwell_time_seconds: 0,
      });
      hasTrackedViewRef.current = true;
      startTimeRef.current = Date.now();
    }

    // 2. Track dwell time on cleanup/unmount
    return () => {
      if (startTimeRef.current && articleId) {
        const elapsedSeconds = Math.round((Date.now() - startTimeRef.current) / 1000);
        // Only send read event if user stayed at least 2 seconds, capped at 4 hours
        if (elapsedSeconds >= 2 && elapsedSeconds <= 14400) {
          recordReadingEventApi({
            article_id: articleId,
            event_type: 'read',
            dwell_time_seconds: elapsedSeconds,
          });
        }
      }
    };
  }, [articleId, isAuthenticated]);
}

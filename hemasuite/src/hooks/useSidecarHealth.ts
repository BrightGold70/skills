import { useEffect, useRef, useState } from "react";

const HEALTH_URL = "http://127.0.0.1:9720/health";
const DEFAULT_POLL_MS = 1000;

export function useSidecarHealth(pollMs = DEFAULT_POLL_MS) {
  const [ready, setReady] = useState(false);
  const cancelledRef = useRef(false);

  useEffect(() => {
    if (ready) return;
    cancelledRef.current = false;

    let timeoutId: ReturnType<typeof setTimeout>;

    const poll = async () => {
      if (cancelledRef.current) return;
      try {
        const resp = await fetch(HEALTH_URL);
        if (!cancelledRef.current && resp.ok) {
          setReady(true);
          return;
        }
      } catch {
        // sidecar not up yet
      }
      if (!cancelledRef.current) {
        timeoutId = setTimeout(poll, pollMs);
      }
    };

    poll();

    return () => {
      cancelledRef.current = true;
      clearTimeout(timeoutId);
    };
  }, [ready, pollMs]);

  return { ready };
}

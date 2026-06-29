"use client";

import * as React from "react";

import { API_BASE } from "@/lib/api/config";
import { getToken } from "@/lib/api/token";
import type { JobStatus } from "@/lib/api/jobs";

export interface JobProgressEvent {
  id: string;
  status: JobStatus;
  progress: number;
  error: string | null;
  result_asset_id: string | null;
}

const TERMINAL: JobStatus[] = ["succeeded", "failed", "cancelled"];

function wsBase(): string {
  return API_BASE.replace(/^http/, "ws");
}

/**
 * Subscribes to live progress for a single job over WebSocket.
 * Pass `null` to disable. Calls `onDone` once when the job reaches a
 * terminal state.
 */
export function useJobProgress(
  jobId: string | null,
  onDone?: (event: JobProgressEvent) => void,
) {
  const [event, setEvent] = React.useState<JobProgressEvent | null>(null);
  const onDoneRef = React.useRef(onDone);
  React.useEffect(() => {
    onDoneRef.current = onDone;
  });

  React.useEffect(() => {
    if (!jobId) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setEvent(null);
      return;
    }
    const token = getToken();
    if (!token) return;

    const url = `${wsBase()}/api/v1/ws/jobs/${jobId}?token=${encodeURIComponent(token)}`;
    const socket = new WebSocket(url);

    socket.onmessage = (msg) => {
      try {
        const data: JobProgressEvent = JSON.parse(msg.data);
        setEvent(data);
        if (TERMINAL.includes(data.status)) {
          onDoneRef.current?.(data);
        }
      } catch {
        /* ignore malformed frames */
      }
    };

    return () => {
      socket.close();
    };
  }, [jobId]);

  return event;
}

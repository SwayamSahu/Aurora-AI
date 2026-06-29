/**
 * Option catalogs and defaults for the Notifications and Playback / Export
 * settings sections. These persist into the user's free-form `preferences`
 * JSON (merged server-side), keyed under `notifications` and `playback`.
 */

/* ------------------------------------------------------------------ *
 * Notifications
 * ------------------------------------------------------------------ */
export interface NotificationToggle {
  key: keyof NotificationPrefs;
  label: string;
  description: string;
}

export interface NotificationPrefs {
  job_complete: boolean;
  job_failed: boolean;
  export_ready: boolean;
  product_updates: boolean;
}

export const DEFAULT_NOTIFICATIONS: NotificationPrefs = {
  job_complete: true,
  job_failed: true,
  export_ready: true,
  product_updates: false,
};

export const NOTIFICATION_TOGGLES: NotificationToggle[] = [
  {
    key: "job_complete",
    label: "Generation finished",
    description: "Notify me when a video, image, voice or music job completes.",
  },
  {
    key: "job_failed",
    label: "Generation failed",
    description: "Alert me when a job errors out so I can retry quickly.",
  },
  {
    key: "export_ready",
    label: "Export ready",
    description: "Tell me when a timeline export has finished rendering.",
  },
  {
    key: "product_updates",
    label: "Product updates",
    description: "Occasional notes about new models and Aurora features.",
  },
];

/* ------------------------------------------------------------------ *
 * Playback & Export
 * ------------------------------------------------------------------ */
export interface PlaybackPrefs {
  autoplay_previews: boolean;
  loop_previews: boolean;
  export_format: string;
  export_quality: string;
}

export const DEFAULT_PLAYBACK: PlaybackPrefs = {
  autoplay_previews: true,
  loop_previews: true,
  export_format: "mp4",
  export_quality: "high",
};

export const EXPORT_FORMATS = [
  { value: "mp4", label: "MP4 (H.264)" },
  { value: "webm", label: "WebM (VP9)" },
  { value: "mov", label: "MOV (ProRes-friendly)" },
] as const;

export const EXPORT_QUALITIES = [
  { value: "high", label: "High — crisp, larger file" },
  { value: "balanced", label: "Balanced — good quality/size" },
  { value: "compact", label: "Compact — smallest file" },
] as const;

export const PLAYBACK_TOGGLES: {
  key: "autoplay_previews" | "loop_previews";
  label: string;
  description: string;
}[] = [
  {
    key: "autoplay_previews",
    label: "Autoplay previews",
    description: "Play generated clips automatically in the library and editor.",
  },
  {
    key: "loop_previews",
    label: "Loop previews",
    description: "Repeat short preview clips instead of stopping at the end.",
  },
];

/* ------------------------------------------------------------------ *
 * Readers — pull a typed slice out of the preferences JSON with fallbacks.
 * ------------------------------------------------------------------ */
export function readNotifications(
  prefs: Record<string, unknown> | undefined,
): NotificationPrefs {
  const n = (prefs?.notifications as Partial<NotificationPrefs>) ?? {};
  return { ...DEFAULT_NOTIFICATIONS, ...n };
}

export function readPlayback(
  prefs: Record<string, unknown> | undefined,
): PlaybackPrefs {
  const p = (prefs?.playback as Partial<PlaybackPrefs>) ?? {};
  return { ...DEFAULT_PLAYBACK, ...p };
}

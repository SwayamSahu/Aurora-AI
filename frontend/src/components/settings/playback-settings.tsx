"use client";

import * as React from "react";
import { toast } from "sonner";

import { useAuth } from "@/components/auth/auth-provider";
import { updateProfile } from "@/lib/api/auth";
import { ApiError } from "@/lib/api/client";
import {
  EXPORT_FORMATS,
  EXPORT_QUALITIES,
  PLAYBACK_TOGGLES,
  type PlaybackPrefs,
  readPlayback,
} from "@/lib/settings-options";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export function PlaybackSettings() {
  const { user, setUser } = useAuth();
  const initial = readPlayback(user?.preferences);
  const [values, setValues] = React.useState<PlaybackPrefs>(initial);
  const [saving, setSaving] = React.useState(false);

  const dirty =
    values.autoplay_previews !== initial.autoplay_previews ||
    values.loop_previews !== initial.loop_previews ||
    values.export_format !== initial.export_format ||
    values.export_quality !== initial.export_quality;

  function set<K extends keyof PlaybackPrefs>(key: K, v: PlaybackPrefs[K]) {
    setValues((prev) => ({ ...prev, [key]: v }));
  }

  async function onSave() {
    setSaving(true);
    try {
      const updated = await updateProfile({
        preferences: { playback: values },
      });
      setUser(updated);
      toast.success("Playback & export defaults saved.");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Save failed.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Playback &amp; export</CardTitle>
        <CardDescription>
          How previews behave in the app, and the defaults used when you export
          a timeline.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="divide-y divide-border">
          {PLAYBACK_TOGGLES.map((t) => (
            <div
              key={t.key}
              className="flex items-center justify-between gap-6 py-4 first:pt-0"
            >
              <div className="space-y-0.5">
                <Label htmlFor={`play-${t.key}`} className="cursor-pointer">
                  {t.label}
                </Label>
                <p className="text-sm text-muted-foreground">{t.description}</p>
              </div>
              <Switch
                id={`play-${t.key}`}
                checked={values[t.key]}
                onCheckedChange={(v) => set(t.key, v)}
              />
            </div>
          ))}
        </div>

        <div className="grid gap-5 sm:grid-cols-2">
          <div className="space-y-1.5">
            <Label>Default export format</Label>
            <Select
              value={values.export_format}
              onValueChange={(v) => set("export_format", v)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {EXPORT_FORMATS.map((f) => (
                  <SelectItem key={f.value} value={f.value}>
                    {f.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-1.5">
            <Label>Export quality</Label>
            <Select
              value={values.export_quality}
              onValueChange={(v) => set("export_quality", v)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {EXPORT_QUALITIES.map((q) => (
                  <SelectItem key={q.value} value={q.value}>
                    {q.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardContent>
      <CardFooter className="justify-end">
        <Button onClick={onSave} loading={saving} disabled={!dirty}>
          Save defaults
        </Button>
      </CardFooter>
    </Card>
  );
}

"use client";

import * as React from "react";
import { toast } from "sonner";

import { useAuth } from "@/components/auth/auth-provider";
import { updateProfile } from "@/lib/api/auth";
import { ApiError } from "@/lib/api/client";
import {
  DEFAULT_GENERATION,
  DURATIONS,
  type GenerationDefaults,
  RESOLUTIONS,
  VIDEO_MODELS,
} from "@/lib/generation-options";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
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

function readDefaults(prefs: Record<string, unknown> | undefined): GenerationDefaults {
  return {
    default_model:
      (prefs?.default_model as string) ?? DEFAULT_GENERATION.default_model,
    default_resolution:
      (prefs?.default_resolution as string) ??
      DEFAULT_GENERATION.default_resolution,
    default_duration:
      (prefs?.default_duration as string) ?? DEFAULT_GENERATION.default_duration,
  };
}

export function GenerationSettings() {
  const { user, setUser } = useAuth();
  const initial = readDefaults(user?.preferences);
  const [values, setValues] = React.useState<GenerationDefaults>(initial);
  const [saving, setSaving] = React.useState(false);

  const dirty =
    values.default_model !== initial.default_model ||
    values.default_resolution !== initial.default_resolution ||
    values.default_duration !== initial.default_duration;

  function set<K extends keyof GenerationDefaults>(key: K, v: string) {
    setValues((prev) => ({ ...prev, [key]: v }));
  }

  async function onSave() {
    setSaving(true);
    try {
      const updated = await updateProfile({
        preferences: { ...values } as Record<string, unknown>,
      });
      setUser(updated);
      toast.success("Generation defaults saved.");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Save failed.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Generation defaults</CardTitle>
        <CardDescription>
          Pre-filled when you start a new generation. You can override these per
          clip.
        </CardDescription>
      </CardHeader>
      <CardContent className="grid gap-5 sm:grid-cols-3">
        <div className="space-y-1.5">
          <Label>Default model</Label>
          <Select
            value={values.default_model}
            onValueChange={(v) => set("default_model", v)}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {VIDEO_MODELS.map((m) => (
                <SelectItem key={m.value} value={m.value}>
                  {m.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-1.5">
          <Label>Resolution</Label>
          <Select
            value={values.default_resolution}
            onValueChange={(v) => set("default_resolution", v)}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {RESOLUTIONS.map((r) => (
                <SelectItem key={r.value} value={r.value}>
                  {r.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-1.5">
          <Label>Duration</Label>
          <Select
            value={values.default_duration}
            onValueChange={(v) => set("default_duration", v)}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {DURATIONS.map((d) => (
                <SelectItem key={d.value} value={d.value}>
                  {d.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
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

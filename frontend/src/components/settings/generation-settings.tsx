"use client";

import * as React from "react";
import { toast } from "sonner";

import { useAuth } from "@/components/auth/auth-provider";
import { updateProfile } from "@/lib/api/auth";
import { ApiError } from "@/lib/api/client";
import {
  ASPECT_RATIOS,
  aspectFromLegacyResolution,
  DEFAULT_GENERATION,
  durationOptionsFor,
  type GenerationDefaults,
} from "@/lib/generation-options";
import { useVideoModels } from "@/lib/query/generation";
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
  // Back-compat: older saved prefs stored a "WxH" resolution string instead
  // of an aspect ratio id — map it to the closest aspect so it keeps working.
  const legacyResolution = prefs?.default_resolution as string | undefined;
  return {
    default_model:
      (prefs?.default_model as string) ?? DEFAULT_GENERATION.default_model,
    default_aspect:
      (prefs?.default_aspect as string) ??
      (legacyResolution
        ? aspectFromLegacyResolution(legacyResolution)
        : DEFAULT_GENERATION.default_aspect),
    default_duration:
      (prefs?.default_duration as string) ?? DEFAULT_GENERATION.default_duration,
  };
}

export function GenerationSettings() {
  const { user, setUser } = useAuth();
  const initial = readDefaults(user?.preferences);
  const [values, setValues] = React.useState<GenerationDefaults>(initial);
  const [saving, setSaving] = React.useState(false);

  const models = useVideoModels().data ?? [];
  const durationOptions = durationOptionsFor(
    models.find((m) => m.id === values.default_model),
  );

  const dirty =
    values.default_model !== initial.default_model ||
    values.default_aspect !== initial.default_aspect ||
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
              {models.map((m) => (
                <SelectItem key={m.id} value={m.id}>
                  {m.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-1.5">
          <Label>Aspect ratio</Label>
          <Select
            value={values.default_aspect}
            onValueChange={(v) => set("default_aspect", v)}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {ASPECT_RATIOS.map((a) => (
                <SelectItem key={a.id} value={a.id}>
                  {a.label}
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
              {durationOptions.map((d) => (
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

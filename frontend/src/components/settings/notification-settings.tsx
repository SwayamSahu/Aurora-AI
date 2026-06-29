"use client";

import * as React from "react";
import { toast } from "sonner";

import { useAuth } from "@/components/auth/auth-provider";
import { updateProfile } from "@/lib/api/auth";
import { ApiError } from "@/lib/api/client";
import {
  NOTIFICATION_TOGGLES,
  type NotificationPrefs,
  readNotifications,
} from "@/lib/settings-options";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

export function NotificationSettings() {
  const { user, setUser } = useAuth();
  const initial = readNotifications(user?.preferences);
  const [values, setValues] = React.useState<NotificationPrefs>(initial);
  const [saving, setSaving] = React.useState(false);

  const dirty = NOTIFICATION_TOGGLES.some(
    (t) => values[t.key] !== initial[t.key],
  );

  function toggle(key: keyof NotificationPrefs, v: boolean) {
    setValues((prev) => ({ ...prev, [key]: v }));
  }

  async function onSave() {
    setSaving(true);
    try {
      const updated = await updateProfile({
        preferences: { notifications: values },
      });
      setUser(updated);
      toast.success("Notification preferences saved.");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Save failed.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Notifications</CardTitle>
        <CardDescription>
          Choose what Aurora should let you know about while you work.
        </CardDescription>
      </CardHeader>
      <CardContent className="divide-y divide-border">
        {NOTIFICATION_TOGGLES.map((t) => (
          <div
            key={t.key}
            className="flex items-center justify-between gap-6 py-4 first:pt-0 last:pb-0"
          >
            <div className="space-y-0.5">
              <Label htmlFor={`notif-${t.key}`} className="cursor-pointer">
                {t.label}
              </Label>
              <p className="text-sm text-muted-foreground">{t.description}</p>
            </div>
            <Switch
              id={`notif-${t.key}`}
              checked={values[t.key]}
              onCheckedChange={(v) => toggle(t.key, v)}
            />
          </div>
        ))}
      </CardContent>
      <CardFooter className="justify-end">
        <Button onClick={onSave} loading={saving} disabled={!dirty}>
          Save preferences
        </Button>
      </CardFooter>
    </Card>
  );
}

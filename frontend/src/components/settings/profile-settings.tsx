"use client";

import * as React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";

import { useAuth } from "@/components/auth/auth-provider";
import { updateProfile } from "@/lib/api/auth";
import { ApiError } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";

const schema = z.object({ full_name: z.string().min(1, "Enter your name.") });
type Values = z.infer<typeof schema>;

export function ProfileSettings() {
  const { user, setUser } = useAuth();
  const form = useForm<Values>({
    resolver: zodResolver(schema),
    values: { full_name: user?.full_name ?? "" },
  });

  async function onSubmit(values: Values) {
    try {
      const updated = await updateProfile({ full_name: values.full_name });
      setUser(updated);
      toast.success("Profile updated.");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Update failed.");
    }
  }

  const memberSince = user?.created_at
    ? new Date(user.created_at).toLocaleDateString(undefined, {
        year: "numeric",
        month: "long",
        day: "numeric",
      })
    : "—";

  return (
    <div className="space-y-6">
    <Card>
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)}>
          <CardHeader>
            <CardTitle>Profile</CardTitle>
            <CardDescription>
              Your name and account email.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <FormField
              control={form.control}
              name="full_name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Full name</FormLabel>
                  <FormControl>
                    <Input {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" value={user?.email ?? ""} disabled readOnly />
              <p className="text-xs text-muted-foreground">
                Email changes aren&apos;t supported yet.
              </p>
            </div>
          </CardContent>
          <CardFooter className="justify-end">
            <Button
              type="submit"
              loading={form.formState.isSubmitting}
              disabled={!form.formState.isDirty}
            >
              Save changes
            </Button>
          </CardFooter>
        </form>
      </Form>
    </Card>

      <Card>
        <CardHeader>
          <CardTitle>Account</CardTitle>
          <CardDescription>Details about this Aurora account.</CardDescription>
        </CardHeader>
        <CardContent className="divide-y divide-border text-sm">
          <div className="flex items-center justify-between py-3 first:pt-0">
            <span className="text-muted-foreground">Account type</span>
            <span className="inline-flex items-center gap-1.5 rounded-full bg-primary/10 px-2.5 py-0.5 text-xs font-medium text-primary">
              {user?.is_superuser ? "Administrator" : "Self-hosted"}
            </span>
          </div>
          <div className="flex items-center justify-between py-3">
            <span className="text-muted-foreground">Member since</span>
            <span className="font-medium">{memberSince}</span>
          </div>
          <div className="flex items-center justify-between gap-4 py-3 last:pb-0">
            <span className="text-muted-foreground">User ID</span>
            <span className="truncate font-mono text-xs text-foreground/80">
              {user?.id ?? "—"}
            </span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

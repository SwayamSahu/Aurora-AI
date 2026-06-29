"use client";

import * as React from "react";
import Link from "next/link";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { ArrowLeft, MailCheck } from "lucide-react";

import { requestPasswordReset } from "@/lib/api/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";

const schema = z.object({ email: z.string().email("Enter a valid email.") });
type Values = z.infer<typeof schema>;

export default function ForgotPasswordPage() {
  const [sent, setSent] = React.useState(false);
  // Dev only: the backend returns a reset token when email delivery is off.
  const [devToken, setDevToken] = React.useState<string | null>(null);

  const form = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: { email: "" },
  });

  async function onSubmit(values: Values) {
    try {
      const res = await requestPasswordReset(values.email);
      setDevToken(res.reset_token);
      setSent(true);
    } catch {
      toast.error("Something went wrong. Please try again.");
    }
  }

  if (sent) {
    return (
      <div className="space-y-6">
        <div className="flex size-12 items-center justify-center rounded-full bg-success/10 text-success">
          <MailCheck className="size-6" />
        </div>
        <div className="space-y-2">
          <h1 className="text-2xl font-semibold tracking-tight">Check your email</h1>
          <p className="text-sm text-muted-foreground">
            If that address is registered, we&apos;ve sent a link to reset your
            password.
          </p>
        </div>
        {devToken ? (
          <div className="rounded-lg border border-warning/40 bg-warning/10 p-3 text-xs">
            <p className="mb-2 font-medium">Development mode (no email sent)</p>
            <Button asChild size="sm" variant="outline">
              <Link href={`/reset-password?token=${devToken}`}>
                Continue to reset password
              </Link>
            </Button>
          </div>
        ) : null}
        <Button asChild variant="ghost" className="w-full">
          <Link href="/login">
            <ArrowLeft className="size-4" /> Back to sign in
          </Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="space-y-2">
        <h1 className="text-2xl font-semibold tracking-tight">
          Reset your password
        </h1>
        <p className="text-sm text-muted-foreground">
          Enter your email and we&apos;ll send you a reset link.
        </p>
      </div>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          <FormField
            control={form.control}
            name="email"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Email</FormLabel>
                <FormControl>
                  <Input
                    type="email"
                    autoComplete="email"
                    placeholder="you@example.com"
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />
          <Button
            type="submit"
            className="w-full"
            loading={form.formState.isSubmitting}
          >
            Send reset link
          </Button>
        </form>
      </Form>

      <Button asChild variant="ghost" className="w-full">
        <Link href="/login">
          <ArrowLeft className="size-4" /> Back to sign in
        </Link>
      </Button>
    </div>
  );
}

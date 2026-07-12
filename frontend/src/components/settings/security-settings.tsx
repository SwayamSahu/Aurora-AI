"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";

import { useAuth } from "@/components/auth/auth-provider";
import { changePassword, eraseMyAccount, exportMyData } from "@/lib/api/auth";
import { ApiError } from "@/lib/api/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";

const schema = z
  .object({
    current_password: z.string().min(1, "Enter your current password."),
    new_password: z.string().min(8, "Use at least 8 characters."),
    confirm: z.string(),
  })
  .refine((v) => v.new_password === v.confirm, {
    message: "Passwords don't match.",
    path: ["confirm"],
  });

type Values = z.infer<typeof schema>;

function ExportDataCard() {
  const [loading, setLoading] = React.useState(false);

  async function download() {
    setLoading(true);
    try {
      const data = await exportMyData();
      const blob = new Blob([JSON.stringify(data, null, 2)], {
        type: "application/json",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `aurora-data-export-${new Date().toISOString().slice(0, 10)}.json`;
      a.click();
      URL.revokeObjectURL(url);
      toast.success("Your data export has downloaded.");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Export failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Your data</CardTitle>
        <CardDescription>
          Download everything Aurora holds about your account — profile,
          posts, listings, orders, and wallet history — as a JSON file.
        </CardDescription>
      </CardHeader>
      <CardFooter className="justify-end">
        <Button variant="outline" onClick={download} loading={loading}>
          Download my data
        </Button>
      </CardFooter>
    </Card>
  );
}

function DeleteAccountDialog() {
  const router = useRouter();
  const { logout } = useAuth();
  const [password, setPassword] = React.useState("");
  const [loading, setLoading] = React.useState(false);
  const [open, setOpen] = React.useState(false);

  async function submit() {
    if (!password) {
      toast.error("Enter your password to confirm.");
      return;
    }
    setLoading(true);
    try {
      await eraseMyAccount(password);
      toast.success("Your account has been deleted.");
      logout();
      router.push("/");
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Deletion failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>
        <Button variant="destructive">Delete account</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Delete account?</DialogTitle>
          <DialogDescription>
            This permanently scrubs your email, name, and password from your
            account and signs you out everywhere. It can&apos;t be undone.
            Enter your password to confirm.
          </DialogDescription>
        </DialogHeader>
        <Input
          type="password"
          placeholder="Password"
          autoComplete="current-password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        <DialogFooter>
          <DialogClose asChild>
            <Button variant="outline">Cancel</Button>
          </DialogClose>
          <Button variant="destructive" onClick={submit} loading={loading}>
            Delete my account
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export function SecuritySettings() {
  const { logout } = useAuth();
  const form = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: { current_password: "", new_password: "", confirm: "" },
  });

  async function onSubmit(values: Values) {
    try {
      await changePassword(values.current_password, values.new_password);
      toast.success("Password changed.");
      form.reset();
    } catch (err) {
      toast.error(err instanceof ApiError ? err.message : "Change failed.");
    }
  }

  return (
    <div className="space-y-6">
      <Card>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)}>
            <CardHeader>
              <CardTitle>Password</CardTitle>
              <CardDescription>
                Change the password used to sign in.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <FormField
                control={form.control}
                name="current_password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Current password</FormLabel>
                    <FormControl>
                      <Input type="password" autoComplete="current-password" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="new_password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>New password</FormLabel>
                    <FormControl>
                      <Input type="password" autoComplete="new-password" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="confirm"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Confirm new password</FormLabel>
                    <FormControl>
                      <Input type="password" autoComplete="new-password" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </CardContent>
            <CardFooter className="justify-end">
              <Button type="submit" loading={form.formState.isSubmitting}>
                Change password
              </Button>
            </CardFooter>
          </form>
        </Form>
      </Card>

      <ExportDataCard />

      <Card className="border-destructive/40">
        <CardHeader>
          <CardTitle className="text-destructive">Danger zone</CardTitle>
          <CardDescription>
            Sign out of this device, or delete your account.
          </CardDescription>
        </CardHeader>
        <CardFooter className="justify-between gap-3">
          <Button variant="outline" onClick={logout}>
            Sign out
          </Button>
          <DeleteAccountDialog />
        </CardFooter>
      </Card>
    </div>
  );
}

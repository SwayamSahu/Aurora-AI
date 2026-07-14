"use client";

import * as React from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { RotateCcw } from "lucide-react";

import { useAuth } from "@/components/auth/auth-provider";
import { isAdmin } from "@/lib/admin/access";
import {
  type AdminModel,
  clearAdminModelOverride,
  listAdminModels,
  updateAdminModel,
} from "@/lib/admin/models";
import { ApiError } from "@/lib/api/client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Switch } from "@/components/ui/switch";

const QUERY_KEY = ["admin-models"];

function ModelRow({ model }: { model: AdminModel }) {
  const qc = useQueryClient();
  const [price, setPrice] = React.useState(String(model.credit_cost));

  const update = useMutation({
    mutationFn: (patch: { enabled?: boolean; credit_cost?: number }) =>
      updateAdminModel(model.id, patch),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QUERY_KEY });
      toast.success(`${model.label} updated.`);
    },
    onError: (err) => {
      toast.error(err instanceof ApiError ? err.message : "Update failed.");
    },
  });

  const reset = useMutation({
    mutationFn: () => clearAdminModelOverride(model.id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: QUERY_KEY });
      toast.success(`${model.label} reverted to catalog default.`);
    },
    onError: (err) => {
      toast.error(err instanceof ApiError ? err.message : "Reset failed.");
    },
  });

  const priceDirty = price !== String(model.credit_cost);

  return (
    <div className="flex flex-wrap items-center gap-4 rounded-xl border border-[var(--mk-border)] bg-[var(--mk-surface-1)] p-4">
      <div className="min-w-[180px] flex-1">
        <div className="flex flex-wrap items-center gap-1.5">
          <p className="font-semibold">{model.label}</p>
          {model.badges.map((b) => (
            <Badge key={b} variant="secondary" className="text-[10px]">
              {b}
            </Badge>
          ))}
          {model.is_overridden ? (
            <Badge variant="outline" className="text-[10px]">
              customized
            </Badge>
          ) : null}
        </div>
        <p className="text-xs text-muted-foreground">
          {model.provider} · {model.kind} · {model.resolution} ·{" "}
          {model.min_duration}–{model.max_duration}s
        </p>
      </div>

      <div className="flex items-center gap-2">
        <span className="text-xs text-muted-foreground">Enabled</span>
        <Switch
          checked={model.enabled}
          onCheckedChange={(checked) => update.mutate({ enabled: checked })}
          disabled={update.isPending}
        />
      </div>

      <div className="flex items-center gap-2">
        <span className="text-xs text-muted-foreground">Credits</span>
        <Input
          value={price}
          onChange={(e) => setPrice(e.target.value.replace(/[^0-9]/g, ""))}
          className="h-8 w-20"
        />
        <Button
          size="sm"
          variant="outline"
          disabled={!priceDirty || !price || update.isPending}
          loading={update.isPending}
          onClick={() => update.mutate({ credit_cost: Number(price) })}
        >
          Save
        </Button>
      </div>

      {model.is_overridden ? (
        <Button
          size="sm"
          variant="ghost"
          aria-label={`Reset ${model.label} to catalog default`}
          loading={reset.isPending}
          onClick={() => reset.mutate()}
        >
          <RotateCcw className="size-3.5" /> Reset
        </Button>
      ) : null}
    </div>
  );
}

export default function AdminModelsPage() {
  const { user, status } = useAuth();

  const { data, isLoading } = useQuery({
    queryKey: QUERY_KEY,
    queryFn: listAdminModels,
    enabled: isAdmin(user),
  });

  if (status === "loading") {
    return (
      <div className="mx-auto w-full max-w-[900px] space-y-3 px-4 py-12">
        <Skeleton className="h-8 w-40" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (status !== "authenticated" || !isAdmin(user)) {
    return (
      <p className="py-24 text-center text-muted-foreground">
        Admin access required.
      </p>
    );
  }

  const local = (data ?? []).filter((m) => m.kind === "local");
  const api = (data ?? []).filter((m) => m.kind === "api");

  return (
    <div className="mx-auto w-full max-w-[900px] px-4 py-12 md:px-8">
      <h1 className="mb-2 text-3xl font-extrabold tracking-tight">
        Video Models
      </h1>
      <p className="mb-6 text-sm text-muted-foreground">
        Enable/disable a model or re-price it — changes apply immediately,
        with no redeploy.
      </p>

      {/* The key includes credit_cost so a row remounts when the server price
          changes (after a Save or a Reset), resetting ModelRow's local price
          input to the fresh value — a bare key={m.id} would leave it stale. */}
      {isLoading ? (
        <Skeleton className="h-64 w-full" />
      ) : (
        <div className="space-y-6">
          <div>
            <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
              Local (Aurora GPU)
            </h2>
            <div className="space-y-2">
              {local.map((m) => (
                <ModelRow key={`${m.id}:${m.credit_cost}`} model={m} />
              ))}
            </div>
          </div>
          <div>
            <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
              Hosted API models
            </h2>
            <div className="space-y-2">
              {api.map((m) => (
                <ModelRow key={`${m.id}:${m.credit_cost}`} model={m} />
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

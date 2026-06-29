"use client";

import * as React from "react";
import { toast } from "sonner";
import { Rocket, Inbox } from "lucide-react";

import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { Skeleton } from "@/components/ui/skeleton";
import { Progress } from "@/components/ui/progress";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
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
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { EmptyState } from "@/components/shared/empty-state";
import { ErrorState } from "@/components/shared/error-state";
import { PageLoader } from "@/components/shared/spinner";

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <section className="space-y-4">
      <h2 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">
        {title}
      </h2>
      <div className="rounded-xl border border-border bg-card p-6">
        {children}
      </div>
    </section>
  );
}

export default function DesignSystemPage() {
  const [progress, setProgress] = React.useState(40);

  return (
    <>
      <PageHeader
        title="Design system"
        description="Living reference for Aurora's components, variants and states."
        actions={<Badge variant="secondary">Phase 0</Badge>}
      />

      <div className="space-y-10">
        <Section title="Colors">
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-6">
            {[
              ["Background", "bg-background"],
              ["Card", "bg-card"],
              ["Primary", "bg-primary"],
              ["Secondary", "bg-secondary"],
              ["Muted", "bg-muted"],
              ["Accent", "bg-accent"],
              ["Destructive", "bg-destructive"],
              ["Success", "bg-success"],
              ["Warning", "bg-warning"],
              ["Border", "bg-border"],
            ].map(([name, cls]) => (
              <div key={name} className="space-y-1.5">
                <div
                  className={`h-12 rounded-lg border border-border ${cls}`}
                />
                <p className="text-xs text-muted-foreground">{name}</p>
              </div>
            ))}
          </div>
        </Section>

        <Section title="Buttons">
          <div className="flex flex-wrap items-center gap-3">
            <Button>Default</Button>
            <Button variant="secondary">Secondary</Button>
            <Button variant="outline">Outline</Button>
            <Button variant="ghost">Ghost</Button>
            <Button variant="destructive">Destructive</Button>
            <Button variant="link">Link</Button>
            <Button loading>Loading</Button>
            <Button disabled>Disabled</Button>
            <Button size="sm">Small</Button>
            <Button size="lg">Large</Button>
          </div>
        </Section>

        <Section title="Badges">
          <div className="flex flex-wrap gap-2">
            <Badge>Default</Badge>
            <Badge variant="secondary">Secondary</Badge>
            <Badge variant="success">Success</Badge>
            <Badge variant="warning">Warning</Badge>
            <Badge variant="destructive">Destructive</Badge>
            <Badge variant="outline">Outline</Badge>
          </div>
        </Section>

        <Section title="Form controls">
          <div className="grid max-w-md gap-4">
            <div className="grid gap-1.5">
              <Label htmlFor="demo-input">Email</Label>
              <Input id="demo-input" placeholder="you@example.com" />
            </div>
            <div className="grid gap-1.5">
              <Label htmlFor="demo-invalid">Invalid input</Label>
              <Input id="demo-invalid" aria-invalid defaultValue="not-an-email" />
            </div>
            <div className="grid gap-1.5">
              <Label htmlFor="demo-textarea">Prompt</Label>
              <Textarea
                id="demo-textarea"
                placeholder="A cinematic drone shot over a misty forest at dawn…"
              />
            </div>
            <div className="flex items-center gap-2">
              <Switch id="demo-switch" defaultChecked />
              <Label htmlFor="demo-switch">Enable auto-captions</Label>
            </div>
          </div>
        </Section>

        <Section title="Feedback — toasts">
          <div className="flex flex-wrap gap-3">
            <Button variant="outline" onClick={() => toast("Clip added to library")}>
              Default toast
            </Button>
            <Button
              variant="outline"
              onClick={() => toast.success("Export complete")}
            >
              Success
            </Button>
            <Button
              variant="outline"
              onClick={() => toast.error("Generation failed")}
            >
              Error
            </Button>
            <Button
              variant="outline"
              onClick={() =>
                toast.warning("GPU worker offline — using mock backend")
              }
            >
              Warning
            </Button>
          </div>
        </Section>

        <Section title="Progress">
          <div className="max-w-md space-y-3">
            <Progress value={progress} />
            <div className="flex gap-2">
              <Button
                size="sm"
                variant="outline"
                onClick={() => setProgress((p) => Math.max(0, p - 10))}
              >
                −10%
              </Button>
              <Button
                size="sm"
                variant="outline"
                onClick={() => setProgress((p) => Math.min(100, p + 10))}
              >
                +10%
              </Button>
            </div>
          </div>
        </Section>

        <Section title="Tabs">
          <Tabs defaultValue="generate" className="max-w-md">
            <TabsList>
              <TabsTrigger value="generate">Generate</TabsTrigger>
              <TabsTrigger value="edit">Edit</TabsTrigger>
              <TabsTrigger value="export">Export</TabsTrigger>
            </TabsList>
            <TabsContent value="generate" className="text-sm text-muted-foreground">
              Generate clips from a prompt.
            </TabsContent>
            <TabsContent value="edit" className="text-sm text-muted-foreground">
              Arrange clips on the timeline.
            </TabsContent>
            <TabsContent value="export" className="text-sm text-muted-foreground">
              Render the final MP4.
            </TabsContent>
          </Tabs>
        </Section>

        <Section title="Overlays — dialog & tooltip">
          <div className="flex flex-wrap gap-3">
            <Dialog>
              <DialogTrigger asChild>
                <Button variant="outline">Open dialog</Button>
              </DialogTrigger>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Delete project?</DialogTitle>
                  <DialogDescription>
                    This action cannot be undone. The project and its generated
                    assets will be permanently removed.
                  </DialogDescription>
                </DialogHeader>
                <DialogFooter>
                  <DialogClose asChild>
                    <Button variant="outline">Cancel</Button>
                  </DialogClose>
                  <DialogClose asChild>
                    <Button variant="destructive">Delete</Button>
                  </DialogClose>
                </DialogFooter>
              </DialogContent>
            </Dialog>

            <Tooltip>
              <TooltipTrigger asChild>
                <Button variant="outline">Hover me</Button>
              </TooltipTrigger>
              <TooltipContent>Renders a tooltip</TooltipContent>
            </Tooltip>
          </div>
        </Section>

        <Section title="Cards">
          <div className="grid gap-4 sm:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Cinematic preset</CardTitle>
                <CardDescription>
                  Warm tones, shallow depth of field, slow camera motion.
                </CardDescription>
              </CardHeader>
              <CardContent className="text-sm text-muted-foreground">
                Tuned for film-like b-roll and establishing shots.
              </CardContent>
              <CardFooter>
                <Button size="sm">Use preset</Button>
              </CardFooter>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle>Loading skeleton</CardTitle>
                <CardDescription>Placeholder while data loads.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-4 w-1/2" />
                <Skeleton className="h-24 w-full" />
              </CardContent>
            </Card>
          </div>
        </Section>

        <Section title="States — empty, error, loading">
          <div className="grid gap-4 lg:grid-cols-3">
            <EmptyState
              icon={Inbox}
              title="Nothing here yet"
              description="Empty state with an optional call to action."
              action={<Button size="sm">Create</Button>}
            />
            <ErrorState
              description="Failed to load assets."
              onRetry={() => toast("Retrying…")}
            />
            <div className="rounded-xl border border-border">
              <PageLoader label="Generating preview…" />
            </div>
          </div>
        </Section>

        <Separator />

        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <Rocket className="size-4" />
          This page is the Phase 0 acceptance surface — every component renders
          in light and dark themes.
        </div>
      </div>
    </>
  );
}

"use client";

import Link from "next/link";
import {
  Sparkles,
  FolderKanban,
  Film,
  Plus,
  ArrowRight,
  Wand2,
  Image as ImageIcon,
  Library,
} from "lucide-react";

import { useProjects } from "@/lib/query/projects";
import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/shared/empty-state";
import { ProjectCard } from "@/components/projects/project-card";

const startOptions = [
  {
    title: "Text to video",
    description: "Describe a scene and generate a clip from a prompt.",
    icon: Wand2,
    href: "/studio?mode=text",
  },
  {
    title: "Image to video",
    description: "Animate a still image into a short motion clip.",
    icon: ImageIcon,
    href: "/studio?mode=image",
  },
  {
    title: "Blank timeline",
    description: "Start from an empty project and build it up.",
    icon: Film,
    href: "/studio?mode=blank",
  },
];

export default function DashboardPage() {
  const { data: projects, isLoading } = useProjects("", "recent");

  const projectCount = projects?.length ?? 0;
  const assetCount =
    projects?.reduce((sum, p) => sum + (p.asset_count ?? 0), 0) ?? 0;
  const recent = projects?.slice(0, 4) ?? [];

  const stats = [
    { label: "Projects", value: projectCount, icon: FolderKanban },
    { label: "Assets", value: assetCount, icon: Library },
    { label: "Videos exported", value: 0, icon: Film },
  ];

  return (
    <>
      <PageHeader
        title="Dashboard"
        description="Welcome back. Create a new video or pick up where you left off."
        actions={
          <Button asChild>
            <Link href="/studio">
              <Plus className="size-4" />
              New video
            </Link>
          </Button>
        }
      />

      <div className="grid gap-4 sm:grid-cols-3">
        {stats.map((s) => (
          <Card key={s.label}>
            <CardContent className="flex items-center gap-4 p-5">
              <div className="flex size-11 items-center justify-center rounded-lg bg-accent text-accent-foreground">
                <s.icon className="size-5" />
              </div>
              <div>
                {isLoading ? (
                  <Skeleton className="h-8 w-10" />
                ) : (
                  <p className="text-2xl font-semibold">{s.value}</p>
                )}
                <p className="text-sm text-muted-foreground">{s.label}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <section className="mt-10">
        <div className="mb-4 flex items-center gap-2">
          <Sparkles className="size-4 text-primary" />
          <h2 className="text-lg font-semibold">Start a new video</h2>
        </div>
        <div className="grid gap-4 md:grid-cols-3">
          {startOptions.map((o) => (
            <Link key={o.title} href={o.href} className="group">
              <Card className="h-full transition-colors hover:border-primary/50 hover:bg-accent/30">
                <CardHeader>
                  <div className="mb-2 flex size-10 items-center justify-center rounded-lg bg-primary/10 text-primary">
                    <o.icon className="size-5" />
                  </div>
                  <CardTitle className="flex items-center gap-2 text-base">
                    {o.title}
                    <ArrowRight className="size-4 -translate-x-1 opacity-0 transition-all group-hover:translate-x-0 group-hover:opacity-100" />
                  </CardTitle>
                  <CardDescription>{o.description}</CardDescription>
                </CardHeader>
              </Card>
            </Link>
          ))}
        </div>
      </section>

      <section className="mt-10">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Recent projects</h2>
          {projectCount > 0 ? (
            <Button asChild variant="ghost" size="sm">
              <Link href="/projects">
                View all <ArrowRight className="size-4" />
              </Link>
            </Button>
          ) : null}
        </div>

        {isLoading ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="aspect-video w-full rounded-xl" />
            ))}
          </div>
        ) : recent.length > 0 ? (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {recent.map((p) => (
              <ProjectCard key={p.id} project={p} />
            ))}
          </div>
        ) : (
          <EmptyState
            icon={FolderKanban}
            title="No projects yet"
            description="Your generated videos and edits will appear here once you create your first project."
            action={
              <Button asChild>
                <Link href="/projects">
                  <Plus className="size-4" />
                  Create your first project
                </Link>
              </Button>
            }
          />
        )}
      </section>
    </>
  );
}

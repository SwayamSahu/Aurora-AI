import {
  LayoutDashboard,
  FolderKanban,
  Sparkles,
  ListChecks,
  Settings,
  Palette,
  type LucideIcon,
} from "lucide-react";

export interface NavItem {
  title: string;
  href: string;
  icon: LucideIcon;
  /** Optional keyboard shortcut hint shown in the command palette. */
  shortcut?: string;
}

export interface NavSection {
  label: string;
  items: NavItem[];
}

export const navSections: NavSection[] = [
  {
    label: "Workspace",
    items: [
      { title: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
      { title: "Projects", href: "/projects", icon: FolderKanban },
      { title: "Generate", href: "/studio", icon: Sparkles },
      { title: "Jobs", href: "/jobs", icon: ListChecks },
    ],
  },
  {
    label: "System",
    items: [
      { title: "Settings", href: "/settings", icon: Settings },
      { title: "Design System", href: "/design", icon: Palette },
    ],
  },
];

export const allNavItems: NavItem[] = navSections.flatMap((s) => s.items);

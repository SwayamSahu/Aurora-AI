/**
 * Resolves the string icon names used in `content.ts` to lucide-react
 * components. Keeping this in one place lets the content file stay free of
 * imports/JSX so it can be shared by server and client components.
 */

import {
  BookOpen,
  Captions,
  Code2,
  Download,
  Film,
  Image,
  Layers,
  Mic,
  Music,
  Newspaper,
  PenLine,
  Scissors,
  Shield,
  Sparkles,
  Trophy,
  Video,
  Wand2,
  Workflow,
  Zap,
  type LucideIcon,
} from "lucide-react";

const ICONS: Record<string, LucideIcon> = {
  BookOpen,
  Captions,
  Code2,
  Download,
  Film,
  Image,
  Layers,
  Mic,
  Music,
  Newspaper,
  PenLine,
  Scissors,
  Shield,
  Sparkles,
  Trophy,
  Video,
  Wand2,
  Workflow,
  Zap,
};

/** Look up an icon by name, falling back to Sparkles if unknown. */
export function landingIcon(name: string): LucideIcon {
  return ICONS[name] ?? Sparkles;
}

/**
 * Resolves the string icon names used in `content.ts` to lucide-react
 * components. Keeping this in one place lets the content file stay free of
 * imports/JSX so it can be shared by server and client components.
 */

import {
  Captions,
  Code2,
  Download,
  Film,
  Image,
  Layers,
  Mic,
  Music,
  Scissors,
  Shield,
  Sparkles,
  Video,
  Wand2,
  Zap,
  type LucideIcon,
} from "lucide-react";

const ICONS: Record<string, LucideIcon> = {
  Captions,
  Code2,
  Download,
  Film,
  Image,
  Layers,
  Mic,
  Music,
  Scissors,
  Shield,
  Sparkles,
  Video,
  Wand2,
  Zap,
};

/** Look up an icon by name, falling back to Sparkles if unknown. */
export function landingIcon(name: string): LucideIcon {
  return ICONS[name] ?? Sparkles;
}

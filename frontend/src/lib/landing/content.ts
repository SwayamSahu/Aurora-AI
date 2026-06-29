/**
 * Aurora landing page — single source of truth.
 *
 * EVERY piece of copy, link, model, feature, stat and footer entry on the
 * marketing landing page is defined here.  To rebrand or re-message the page,
 * edit this file only — no component changes required.
 *
 * Icons are referenced by their lucide-react export name (string) and resolved
 * centrally in `icon-map.ts`, so this file stays free of JSX/imports and can be
 * imported from both server and client components.
 */

export interface LandingLink {
  label: string;
  href: string;
  /** When true the link points outside the app (new tab). */
  external?: boolean;
}

export interface LandingFeature {
  icon: string;
  title: string;
  description: string;
  /** Optional short status tag, e.g. "New" or "Beta". */
  tag?: string;
}

export interface LandingModel {
  name: string;
  kind: string;
  icon: string;
}

export interface LandingTab {
  id: string;
  label: string;
  icon: string;
  heading: string;
  body: string;
  bullets: string[];
}

export interface LandingStat {
  value: string;
  label: string;
}

export interface LandingStep {
  icon: string;
  title: string;
  description: string;
}

export interface LandingTestimonial {
  quote: string;
  name: string;
  role: string;
}

export interface LandingFaq {
  question: string;
  answer: string;
}

export interface FooterColumn {
  title: string;
  links: LandingLink[];
}

/* ------------------------------------------------------------------ *
 * Brand
 * ------------------------------------------------------------------ */
export const brand = {
  name: "Aurora",
  tagline: "The open studio for AI video.",
  /** Used in <title> and social previews. */
  metaTitle: "Aurora — The open studio for AI video",
  metaDescription:
    "Generate, voice, caption and edit cinematic video with open models — all on a professional timeline. Fully open source. No vendor lock-in.",
  email: "hello@aurora.video",
  social: {
    github: "https://github.com/aurora-video/aurora",
    x: "https://x.com/aurora_video",
    discord: "https://discord.gg/aurora",
  },
};

/* ------------------------------------------------------------------ *
 * Navigation
 * ------------------------------------------------------------------ */
export const navLinks: LandingLink[] = [
  { label: "Features", href: "#features" },
  { label: "Models", href: "#models" },
  { label: "Workflow", href: "#workflow" },
  { label: "Open source", href: "#open-source" },
  { label: "FAQ", href: "#faq" },
];

export const cta = {
  primary: { label: "Start creating", href: "/signup" },
  secondary: { label: "Open the app", href: "/dashboard" },
  login: { label: "Log in", href: "/login" },
  ghost: { label: "Watch the reel", href: "#showreel" },
};

/* ------------------------------------------------------------------ *
 * Hero
 * ------------------------------------------------------------------ */
export const hero = {
  eyebrow: "Open source · Self-hostable",
  // Two-line headline; the second line is gradient-accented in the component.
  titleLead: "A new frontier for",
  titleAccent: "AI video creation.",
  subtitle:
    "Aurora turns a single prompt into finished video — generate footage, animate stills, add a voiceover, auto-caption it and cut it together on a real timeline. Built entirely on open models you own.",
  // Small trust line under the CTAs.
  note: "Free forever for self-hosting · No credit card · Runs on your GPU",
};

/* ------------------------------------------------------------------ *
 * Media assets
 * Self-hosted, royalty-free (Pexels License) clips + poster frames.
 * Files live in /public/media — see public/media/CREDITS.md.
 * Swap an asset by replacing the file and editing the path here only.
 * ------------------------------------------------------------------ */
export interface LandingMedia {
  /** Path under /public, e.g. "/media/hero-ocean.mp4". */
  src: string;
  /** Poster frame shown before the video plays / when motion is reduced. */
  poster: string;
  /** Accessible description of the footage. */
  alt: string;
}

export const media = {
  /**
   * Hero showreel — cinematic clips cycled as a crossfading slideshow.
   * Add or remove entries freely; the player adapts to the array length.
   */
  showreel: [
    {
      src: "/media/hero-ocean.mp4",
      poster: "/media/hero-ocean.jpg",
      alt: "Cinematic aerial footage of ocean waves and sea foam",
    },
    {
      src: "/media/hero-forest.mp4",
      poster: "/media/hero-forest.jpg",
      alt: "Misty forested mountain valley at dawn",
    },
    {
      src: "/media/hero-coast.mp4",
      poster: "/media/hero-coast.jpg",
      alt: "Aerial drone view of a coastline at sunrise",
    },
    {
      src: "/media/hero-city.mp4",
      poster: "/media/hero-city.jpg",
      alt: "Futuristic neon city skyline after dark",
    },
  ] as LandingMedia[],
  /** Visual for each interactive feature tab, keyed by tab id. */
  featureTab: {
    generate: {
      src: "/media/generate-ink.mp4",
      poster: "/media/generate-ink.jpg",
      alt: "Colorful ink blooming through water",
    },
    image: {
      src: "/media/imagine-paint.mp4",
      poster: "/media/imagine-paint.jpg",
      alt: "Blue paint diffusing through clear water",
    },
    voice: {
      src: "/media/voice-ink.mp4",
      poster: "/media/voice-ink.jpg",
      alt: "Abstract ink swirling in slow motion",
    },
    caption: {
      src: "/media/caption-city.mp4",
      poster: "/media/caption-city.jpg",
      alt: "Busy city crossing lit up at night",
    },
    edit: {
      src: "/media/edit-neon.mp4",
      poster: "/media/edit-neon.jpg",
      alt: "Neon-lit futuristic cityscape at night",
    },
  } as Record<string, LandingMedia>,
};

/* ------------------------------------------------------------------ *
 * Ecosystem strip (honest tech stack, not fabricated customer logos)
 * ------------------------------------------------------------------ */
export const ecosystem = {
  label: "Built on the best of open source",
  items: [
    "FFmpeg",
    "PyTorch",
    "Hugging Face",
    "FastAPI",
    "Next.js",
    "PostgreSQL",
    "Docker",
    "Celery",
  ],
};

/* ------------------------------------------------------------------ *
 * Model showcase
 * ------------------------------------------------------------------ */
export const modelsSection = {
  heading: "Every model you need, in one studio.",
  subheading:
    "Aurora orchestrates best-in-class open models behind a single, elegant interface — swap or upgrade any of them without touching your projects.",
  models: [
    { name: "LTX-Video", kind: "Text → Video", icon: "Video" },
    { name: "Stable Video Diffusion", kind: "Image → Video", icon: "Film" },
    { name: "FLUX.1", kind: "Text → Image", icon: "Image" },
    { name: "MusicGen", kind: "Text → Music", icon: "Music" },
    { name: "Kokoro TTS", kind: "Text → Voice", icon: "Mic" },
    { name: "Whisper", kind: "Speech → Captions", icon: "Captions" },
  ] as LandingModel[],
};

/* ------------------------------------------------------------------ *
 * Interactive feature tabs
 * ------------------------------------------------------------------ */
export const featureTabs: LandingTab[] = [
  {
    id: "generate",
    label: "Generate",
    icon: "Sparkles",
    heading: "From prompt to footage in one step",
    body: "Describe a shot and Aurora generates it. Choose resolution, duration and seed, then send the clip straight to your timeline.",
    bullets: [
      "Text-to-video and image-to-video",
      "Per-shot seed control for reproducibility",
      "Live progress while the model renders",
    ],
  },
  {
    id: "image",
    label: "Imagine",
    icon: "Image",
    heading: "Photoreal stills, then bring them to life",
    body: "Generate high-fidelity images with FLUX, then animate any frame into motion with a single click.",
    bullets: [
      "High-resolution text-to-image",
      "One-click image-to-video animation",
      "Style presets for a consistent look",
    ],
  },
  {
    id: "voice",
    label: "Voice",
    icon: "Mic",
    heading: "Natural voiceovers in dozens of voices",
    body: "Type a script and Aurora speaks it in a lifelike voice, dropped onto its own audio track and ready to mix.",
    bullets: [
      "Multilingual neural text-to-speech",
      "Adjustable pace and voice selection",
      "Lands directly on the timeline",
    ],
  },
  {
    id: "caption",
    label: "Caption",
    icon: "Captions",
    heading: "Accurate subtitles, generated automatically",
    body: "Aurora transcribes your audio with Whisper and lays down perfectly timed, fully editable caption clips.",
    bullets: [
      "Word-accurate automatic transcription",
      "Editable, styleable caption clips",
      "Burned-in or sidecar SRT export",
    ],
  },
  {
    id: "edit",
    label: "Edit",
    icon: "Scissors",
    heading: "A real timeline, not a toy",
    body: "Trim, split, snap, layer and cross-fade on a multi-track editor with undo/redo and instant autosave.",
    bullets: [
      "Multi-track, non-destructive editing",
      "Clip-to-clip transitions and fades",
      "Keyboard-first with full undo history",
    ],
  },
];

/* ------------------------------------------------------------------ *
 * Feature-tab HUD
 * The mini "app interface" overlaid on the bottom of each tab's visual.
 * Each entry tells the HUD what to show so the preview feels like the
 * real product working — a prompt rendering, a voice waveform, captions.
 * ------------------------------------------------------------------ */
export interface FeatureHud {
  /** Small status label, e.g. "Generating", "Rendering", "Transcribing". */
  status: string;
  /** Monospace line — the prompt, transcript or track label. */
  line: string;
  /** Which right-hand control to render. */
  kind: "progress" | "waveform" | "timecode";
  /** progress → percent 0-100; timecode → a time string like "00:04.12". */
  value?: number | string;
  /** Optional trailing meta, e.g. a duration or language tag. */
  meta?: string;
}

export const featureHud: Record<string, FeatureHud> = {
  generate: {
    status: "Generating",
    line: "cinematic wave crashing at golden hour, 35mm",
    kind: "progress",
    value: 72,
    meta: "1080p",
  },
  image: {
    status: "Rendering",
    line: "lone explorer on a dune, volumetric dusk light",
    kind: "progress",
    value: 88,
    meta: "FLUX.1",
  },
  voice: {
    status: "Narrator · Warm",
    line: "“A new frontier for AI video creation.”",
    kind: "waveform",
    meta: "0:12 / 0:24",
  },
  caption: {
    status: "Transcribing",
    line: "built entirely on open models you own",
    kind: "timecode",
    value: "00:04.12",
    meta: "EN",
  },
  edit: {
    status: "Sequence 01",
    line: "wave.mp4 · dunes.mp4 · skyline.mp4",
    kind: "timecode",
    value: "00:12.00",
    meta: "24 fps",
  },
};

/* ------------------------------------------------------------------ *
 * Bento feature grid
 * ------------------------------------------------------------------ */
export const bento = {
  heading: "Everything you need to finish the film.",
  subheading:
    "Aurora is a complete production pipeline — generation, audio, captions, editing and export — not just a model behind a text box.",
  features: [
    {
      icon: "Wand2",
      title: "Prompt to finished cut",
      description:
        "An end-to-end pipeline that takes you from a blank canvas to an exported MP4 without leaving the app.",
      tag: "Core",
    },
    {
      icon: "Layers",
      title: "Multi-track timeline",
      description:
        "Stack video, audio and captions on independent tracks with snapping, trimming and transitions.",
    },
    {
      icon: "Download",
      title: "One-click export",
      description:
        "Render to crisp H.264 MP4 at the resolution and quality you choose, ready to publish anywhere.",
    },
    {
      icon: "Shield",
      title: "Your data, your machine",
      description:
        "Self-host the whole stack. Nothing leaves your infrastructure and there is no per-render bill.",
    },
    {
      icon: "Zap",
      title: "Swappable backends",
      description:
        "Run mock generators on a laptop or real GPU models in production — flip a single environment variable.",
    },
    {
      icon: "Code2",
      title: "Open and extensible",
      description:
        "A clean generator contract lets you plug in new models the day they ship. No black boxes.",
    },
  ] as LandingFeature[],
};

/* ------------------------------------------------------------------ *
 * Workflow / how it works
 * ------------------------------------------------------------------ */
export const workflow = {
  heading: "Three steps from idea to upload.",
  steps: [
    {
      icon: "Sparkles",
      title: "Generate",
      description:
        "Prompt Aurora for video, images, voice and music. Every result lands in your project library.",
    },
    {
      icon: "Scissors",
      title: "Assemble",
      description:
        "Drag clips onto the timeline, add captions and voiceover, then trim and transition to taste.",
    },
    {
      icon: "Download",
      title: "Export",
      description:
        "Render a polished MP4 in a click and ship it — no watermarks, no queues, no lock-in.",
    },
  ] as LandingStep[],
};

/* ------------------------------------------------------------------ *
 * Stats (product-true, not fabricated user counts)
 * ------------------------------------------------------------------ */
export const stats: LandingStat[] = [
  { value: "6", label: "Open models orchestrated" },
  { value: "100%", label: "Open source, MIT-spirited" },
  { value: "4K", label: "Export-ready resolution" },
  { value: "$0", label: "Per-render cost when self-hosted" },
];

/* ------------------------------------------------------------------ *
 * Testimonials
 * NOTE: Replace these with real, attributed quotes before launch.
 * They are illustrative placeholders kept here so the section is
 * fully data-driven.
 * ------------------------------------------------------------------ */
export const testimonials = {
  heading: "Built for creators who want control.",
  items: [
    {
      quote:
        "Finally a generation tool that ends in a real edit, not a one-shot clip I have to fix elsewhere.",
      name: "Maya R.",
      role: "Independent filmmaker",
    },
    {
      quote:
        "We self-host the whole thing. Our footage never leaves our servers and the cost is just electricity.",
      name: "Daniel K.",
      role: "Studio technical director",
    },
    {
      quote:
        "Prompt, voice, captions and a timeline in one place. It collapsed our whole short-form workflow.",
      name: "Priya S.",
      role: "Content lead",
    },
  ] as LandingTestimonial[],
};

/* ------------------------------------------------------------------ *
 * Open-source band
 * ------------------------------------------------------------------ */
export const openSource = {
  eyebrow: "Open source",
  heading: "Own your studio, end to end.",
  body: "Aurora is free and open source. Run it on your own GPU, audit every line, swap any model and extend it however you like. No seats, no metering, no surprises.",
  primary: { label: "Star on GitHub", href: brand.social.github, external: true },
  secondary: { label: "Read the docs", href: "#", external: false },
  points: [
    "Self-host on your hardware in minutes",
    "Swap models with one environment variable",
    "No vendor lock-in, ever",
  ],
};

/* ------------------------------------------------------------------ *
 * FAQ
 * ------------------------------------------------------------------ */
export const faq = {
  heading: "Questions, answered.",
  items: [
    {
      question: "Is Aurora really free?",
      answer:
        "Yes. Aurora is open source and free to self-host. The only cost is the hardware you run the models on.",
    },
    {
      question: "What hardware do I need?",
      answer:
        "You can explore the entire interface on a laptop using mock generators. For real generation, a single NVIDIA GPU with 16 GB of VRAM runs the full model stack.",
    },
    {
      question: "Which models does Aurora use?",
      answer:
        "Aurora orchestrates open models including LTX-Video, Stable Video Diffusion, FLUX.1, MusicGen, Kokoro TTS and Whisper — all swappable behind a clean contract.",
    },
    {
      question: "Does my content leave my machine?",
      answer:
        "No. When self-hosted, every prompt, asset and render stays entirely within your own infrastructure.",
    },
    {
      question: "Can I use Aurora commercially?",
      answer:
        "Aurora itself is open source. Always review the individual licenses of the underlying models for your specific commercial use case.",
    },
  ] as LandingFaq[],
};

/* ------------------------------------------------------------------ *
 * Final CTA
 * ------------------------------------------------------------------ */
export const finalCta = {
  heading: "Start telling stories with Aurora.",
  subheading:
    "Spin up the studio in minutes and turn your next idea into finished video.",
  primary: cta.primary,
  secondary: cta.secondary,
};

/* ------------------------------------------------------------------ *
 * Footer
 * ------------------------------------------------------------------ */
export const footer = {
  blurb: "The open studio for AI video. Generate, edit and export — on your terms.",
  columns: [
    {
      title: "Product",
      links: [
        { label: "Features", href: "#features" },
        { label: "Models", href: "#models" },
        { label: "Workflow", href: "#workflow" },
        { label: "Open the app", href: "/dashboard" },
      ],
    },
    {
      title: "Resources",
      links: [
        { label: "Documentation", href: "#" },
        { label: "GitHub", href: brand.social.github, external: true },
        { label: "Changelog", href: "#" },
        { label: "FAQ", href: "#faq" },
      ],
    },
    {
      title: "Company",
      links: [
        { label: "About", href: "#" },
        { label: "Blog", href: "#" },
        { label: "Contact", href: `mailto:${brand.email}` },
      ],
    },
  ] as FooterColumn[],
  legal: [
    { label: "Privacy", href: "#" },
    { label: "Terms", href: "#" },
    { label: "License", href: brand.social.github, external: true },
  ] as LandingLink[],
  copyright: `© ${new Date().getFullYear()} ${brand.name}. Open source under a permissive license.`,
};

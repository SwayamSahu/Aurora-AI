/**
 * AI Edit — SINGLE SOURCE OF TRUTH for the editing preset catalog.
 *
 * Every capability is data: a preset maps to one of the engine primitives
 * (P1–P8 in the integration plan) plus a mask mode and a prompt template.
 * Adding a feature = adding a row here; no component changes.
 *
 * Face swap is intentionally ABSENT from this catalog — it ships later (E6)
 * behind a consent gate.
 */

/** Engine primitives the backend contract understands. */
export type EditEngine =
  | "segment-track" // P1 — selection/tracking only
  | "inpaint-remove" // P2 — remove + AI fill
  | "masked-v2v" // P3 — masked video-to-video edit
  | "global-restyle" // P4 — full-frame restyle/grade
  | "enhance" // P6 — upscale/denoise/interpolate
  | "retime-camera" // P7 — speed/loop/stabilize/virtual camera
  | "text-ops"; // P8 — OCR-based text edits

/** How the mask is produced for a preset. */
export type MaskMode =
  | "painted" // user paints/selects the region
  | "auto-subject" // segment the main subject
  | "auto-face" // segment face(s)
  | "auto-hair"
  | "auto-clothing"
  | "auto-sky"
  | "auto-background"
  | "auto-text"
  | "full-frame"; // no mask — whole clip

export interface EditPreset {
  id: string;
  label: string;
  /** Catalog section shown in the gallery. */
  category: string;
  engine: EditEngine;
  maskMode: MaskMode;
  /**
   * Prompt template. "{prompt}" is replaced by the user's text; presets
   * without the placeholder run as-is and the prompt box becomes optional.
   */
  prompt: string;
}

export interface EditCategory {
  id: string;
  label: string;
  /** lucide-react icon name, resolved by the gallery. */
  icon: string;
}

export const EDIT_CATEGORIES: EditCategory[] = [
  { id: "transform", label: "Transform", icon: "Wand2" },
  { id: "remove", label: "Remove", icon: "Eraser" },
  { id: "background", label: "Background", icon: "Image" },
  { id: "sky-weather", label: "Sky & Weather", icon: "CloudSun" },
  { id: "time-season", label: "Time & Season", icon: "Sun" },
  { id: "lighting", label: "Lighting", icon: "Lightbulb" },
  { id: "style", label: "Style", icon: "Palette" },
  { id: "people", label: "People", icon: "User" },
  { id: "enhance", label: "Enhance", icon: "Sparkles" },
  { id: "motion-camera", label: "Motion & Camera", icon: "Video" },
  { id: "text", label: "Text", icon: "Type" },
];

/* One-liners keep the catalog scannable; ~120 entries covering the spec. */
// prettier-ignore
export const EDIT_PRESETS: EditPreset[] = [
  /* ---------- Transform (paint an object, describe the change) ---------- */
  { id: "recolor", label: "Change color", category: "transform", engine: "masked-v2v", maskMode: "painted", prompt: "change the color of the selected region to {prompt}, keep lighting and shadows" },
  { id: "retexture", label: "Change texture", category: "transform", engine: "masked-v2v", maskMode: "painted", prompt: "change the texture of the selected region to {prompt}, keep shape and lighting" },
  { id: "rematerial", label: "Change material", category: "transform", engine: "masked-v2v", maskMode: "painted", prompt: "make the selected object out of {prompt}, keep perspective and shadows" },
  { id: "replace-object", label: "Replace object", category: "transform", engine: "masked-v2v", maskMode: "painted", prompt: "replace the selected object with {prompt}, matching perspective, scale, lighting, shadows and motion" },
  { id: "add-object", label: "Add object", category: "transform", engine: "masked-v2v", maskMode: "painted", prompt: "add {prompt} in the selected region, matching scale, lighting and perspective" },
  { id: "replace-animal", label: "Replace animal", category: "transform", engine: "masked-v2v", maskMode: "painted", prompt: "replace the selected animal with {prompt}, preserving its motion, skeleton animation and lighting" },
  { id: "replace-vehicle", label: "Replace vehicle", category: "transform", engine: "masked-v2v", maskMode: "painted", prompt: "replace the selected vehicle with {prompt}, preserving motion, perspective and reflections" },
  { id: "replace-building", label: "Change building", category: "transform", engine: "masked-v2v", maskMode: "painted", prompt: "replace the selected building with {prompt}, matching perspective and lighting" },
  { id: "change-road", label: "Change road", category: "transform", engine: "masked-v2v", maskMode: "painted", prompt: "change the selected road surface to {prompt}, keep perspective" },
  { id: "replace-logo", label: "Replace logo (your asset)", category: "transform", engine: "masked-v2v", maskMode: "painted", prompt: "replace the selected logo with the provided reference logo, tracking its motion, perspective and rotation" },
  { id: "blur-logo", label: "Blur logo", category: "transform", engine: "inpaint-remove", maskMode: "painted", prompt: "blur the selected logo, tracked across the video" },

  /* ------------------------------ Remove ------------------------------- */
  { id: "remove-object", label: "Remove object", category: "remove", engine: "inpaint-remove", maskMode: "painted", prompt: "remove the selected object and fill the region naturally" },
  { id: "remove-people", label: "Remove people", category: "remove", engine: "inpaint-remove", maskMode: "painted", prompt: "remove the selected people and reconstruct the background" },
  { id: "remove-watermark", label: "Remove watermark", category: "remove", engine: "inpaint-remove", maskMode: "painted", prompt: "remove the selected watermark cleanly" },
  { id: "remove-powerlines", label: "Remove power lines", category: "remove", engine: "inpaint-remove", maskMode: "painted", prompt: "remove the selected power lines and wires" },
  { id: "remove-mic", label: "Remove mic / tripod", category: "remove", engine: "inpaint-remove", maskMode: "painted", prompt: "remove the selected equipment (microphone, tripod) from the shot" },
  { id: "remove-reflection", label: "Remove reflection", category: "remove", engine: "inpaint-remove", maskMode: "painted", prompt: "remove the selected reflection while keeping the surface" },
  { id: "remove-shadow", label: "Remove shadow", category: "remove", engine: "inpaint-remove", maskMode: "painted", prompt: "remove the selected shadow and even out the lighting" },
  { id: "remove-trash", label: "Remove clutter", category: "remove", engine: "inpaint-remove", maskMode: "painted", prompt: "remove the selected clutter and debris" },

  /* ---------------------------- Background ----------------------------- */
  { id: "bg-replace", label: "Replace background", category: "background", engine: "masked-v2v", maskMode: "auto-background", prompt: "replace the background with {prompt}, keep the subject and add depth-aware compositing" },
  { id: "bg-beach", label: "Beach", category: "background", engine: "masked-v2v", maskMode: "auto-background", prompt: "replace the background with a sunlit tropical beach, depth-aware" },
  { id: "bg-mountain", label: "Mountains", category: "background", engine: "masked-v2v", maskMode: "auto-background", prompt: "replace the background with misty mountain peaks, depth-aware" },
  { id: "bg-city", label: "City", category: "background", engine: "masked-v2v", maskMode: "auto-background", prompt: "replace the background with a modern city skyline, depth-aware" },
  { id: "bg-mars", label: "Mars", category: "background", engine: "masked-v2v", maskMode: "auto-background", prompt: "replace the background with a red martian landscape, depth-aware" },
  { id: "bg-moon", label: "Moon", category: "background", engine: "masked-v2v", maskMode: "auto-background", prompt: "replace the background with a lunar surface under a black sky" },
  { id: "bg-forest", label: "Forest", category: "background", engine: "masked-v2v", maskMode: "auto-background", prompt: "replace the background with a deep green forest, depth-aware" },
  { id: "bg-studio", label: "Studio", category: "background", engine: "masked-v2v", maskMode: "auto-background", prompt: "replace the background with a clean professional studio backdrop" },
  { id: "bg-greenscreen", label: "Green screen", category: "background", engine: "masked-v2v", maskMode: "auto-background", prompt: "replace the background with a uniform chroma green screen" },
  { id: "bg-room-futuristic", label: "Futuristic room", category: "background", engine: "masked-v2v", maskMode: "auto-background", prompt: "make the room look futuristic with sleek surfaces and ambient light panels" },

  /* --------------------------- Sky & Weather --------------------------- */
  { id: "sky-replace", label: "Replace sky", category: "sky-weather", engine: "masked-v2v", maskMode: "auto-sky", prompt: "replace the sky with {prompt}, matching scene lighting" },
  { id: "sky-sunset", label: "Dramatic sunset", category: "sky-weather", engine: "masked-v2v", maskMode: "auto-sky", prompt: "replace the sky with a dramatic golden sunset, relight the scene warmly" },
  { id: "sky-night", label: "Starry night", category: "sky-weather", engine: "masked-v2v", maskMode: "auto-sky", prompt: "replace the sky with a clear starry night, relight the scene accordingly" },
  { id: "sky-aurora", label: "Aurora", category: "sky-weather", engine: "masked-v2v", maskMode: "auto-sky", prompt: "replace the sky with vivid aurora borealis, cool ambient relight" },
  { id: "sky-storm", label: "Storm clouds", category: "sky-weather", engine: "masked-v2v", maskMode: "auto-sky", prompt: "replace the sky with heavy dramatic storm clouds" },
  { id: "sky-galaxy", label: "Galaxy", category: "sky-weather", engine: "masked-v2v", maskMode: "auto-sky", prompt: "replace the sky with a vivid milky-way galaxy sky" },
  { id: "weather-rain", label: "Rain", category: "sky-weather", engine: "global-restyle", maskMode: "full-frame", prompt: "add realistic rain with wet surfaces and reflections" },
  { id: "weather-snow", label: "Snow", category: "sky-weather", engine: "global-restyle", maskMode: "full-frame", prompt: "add falling snow and settled snow on surfaces" },
  { id: "weather-fog", label: "Fog", category: "sky-weather", engine: "global-restyle", maskMode: "full-frame", prompt: "add soft volumetric fog with depth falloff" },
  { id: "weather-lightning", label: "Lightning", category: "sky-weather", engine: "global-restyle", maskMode: "full-frame", prompt: "add occasional lightning flashes with matching scene illumination" },
  { id: "weather-wind", label: "Wind & leaves", category: "sky-weather", engine: "global-restyle", maskMode: "full-frame", prompt: "add wind: moving foliage and drifting leaves" },
  { id: "weather-fireflies", label: "Fireflies", category: "sky-weather", engine: "global-restyle", maskMode: "full-frame", prompt: "add gently drifting glowing fireflies" },

  /* --------------------------- Time & Season --------------------------- */
  { id: "time-morning", label: "Morning", category: "time-season", engine: "global-restyle", maskMode: "full-frame", prompt: "relight the scene as early morning with soft cool light" },
  { id: "time-noon", label: "Noon", category: "time-season", engine: "global-restyle", maskMode: "full-frame", prompt: "relight the scene as bright midday" },
  { id: "time-golden", label: "Golden hour", category: "time-season", engine: "global-restyle", maskMode: "full-frame", prompt: "relight the scene as warm golden hour with long shadows" },
  { id: "time-blue", label: "Blue hour", category: "time-season", engine: "global-restyle", maskMode: "full-frame", prompt: "relight the scene as dusky blue hour" },
  { id: "time-night", label: "Night", category: "time-season", engine: "global-restyle", maskMode: "full-frame", prompt: "turn the scene into night with practical lights on" },
  { id: "time-rainy-night", label: "Rainy night", category: "time-season", engine: "global-restyle", maskMode: "full-frame", prompt: "turn daytime into a rainy night with wet reflective streets" },
  { id: "season-summer", label: "Summer", category: "time-season", engine: "global-restyle", maskMode: "full-frame", prompt: "transform the season to lush summer" },
  { id: "season-winter", label: "Winter", category: "time-season", engine: "global-restyle", maskMode: "full-frame", prompt: "transform the season to snowy winter" },
  { id: "season-autumn", label: "Autumn", category: "time-season", engine: "global-restyle", maskMode: "full-frame", prompt: "transform the season to golden autumn foliage" },
  { id: "season-spring", label: "Spring", category: "time-season", engine: "global-restyle", maskMode: "full-frame", prompt: "transform the season to blooming spring" },
  { id: "season-xmas", label: "Christmas", category: "time-season", engine: "global-restyle", maskMode: "full-frame", prompt: "add snow and tasteful christmas decorations" },

  /* ----------------------------- Lighting ------------------------------ */
  { id: "light-brighten", label: "Brighten", category: "lighting", engine: "global-restyle", maskMode: "full-frame", prompt: "increase overall brightness naturally, protect highlights" },
  { id: "light-studio", label: "Studio light", category: "lighting", engine: "global-restyle", maskMode: "full-frame", prompt: "relight with clean three-point studio lighting" },
  { id: "light-cinematic", label: "Cinematic", category: "lighting", engine: "global-restyle", maskMode: "full-frame", prompt: "cinematic lighting and color grade: contrast, teal-orange balance, gentle film grain, shallow depth of field" },
  { id: "light-neon", label: "Neon", category: "lighting", engine: "global-restyle", maskMode: "full-frame", prompt: "relight with vivid neon accents, magenta and cyan practicals" },
  { id: "light-soft", label: "Soft light", category: "lighting", engine: "global-restyle", maskMode: "full-frame", prompt: "soft diffused flattering light" },
  { id: "light-golden", label: "Golden light", category: "lighting", engine: "global-restyle", maskMode: "full-frame", prompt: "warm golden light wash" },
  { id: "light-volumetric", label: "Volumetric rays", category: "lighting", engine: "global-restyle", maskMode: "full-frame", prompt: "add volumetric light shafts and god rays" },

  /* ------------------------------- Style ------------------------------- */
  { id: "style-3d-animation", label: "3D animation", category: "style", engine: "global-restyle", maskMode: "full-frame", prompt: "restyle as a polished 3d animated film look, keep motion" },
  { id: "style-anime", label: "Anime", category: "style", engine: "global-restyle", maskMode: "full-frame", prompt: "restyle as high-quality anime, cel shading, keep motion" },
  { id: "style-comic", label: "Comic", category: "style", engine: "global-restyle", maskMode: "full-frame", prompt: "restyle as bold inked comic-book art with halftones" },
  { id: "style-clay", label: "Clay", category: "style", engine: "global-restyle", maskMode: "full-frame", prompt: "restyle as handcrafted claymation" },
  { id: "style-watercolor", label: "Watercolor", category: "style", engine: "global-restyle", maskMode: "full-frame", prompt: "restyle as soft watercolor painting" },
  { id: "style-oil", label: "Oil painting", category: "style", engine: "global-restyle", maskMode: "full-frame", prompt: "restyle as textured oil painting" },
  { id: "style-cyberpunk", label: "Cyberpunk", category: "style", engine: "global-restyle", maskMode: "full-frame", prompt: "restyle as neon cyberpunk with rain-slick streets" },
  { id: "style-noir", label: "Film noir", category: "style", engine: "global-restyle", maskMode: "full-frame", prompt: "restyle as black-and-white film noir with hard shadows" },
  { id: "style-vintage", label: "Vintage film", category: "style", engine: "global-restyle", maskMode: "full-frame", prompt: "restyle as vintage 16mm film with grain and faded color" },
  { id: "style-ghibli-like", label: "Painterly anime", category: "style", engine: "global-restyle", maskMode: "full-frame", prompt: "restyle as painterly hand-drawn animation with lush backgrounds" },
  { id: "style-lowpoly", label: "Low poly", category: "style", engine: "global-restyle", maskMode: "full-frame", prompt: "restyle as low-poly 3d art" },
  { id: "style-voxel", label: "Voxel", category: "style", engine: "global-restyle", maskMode: "full-frame", prompt: "restyle as voxel blocks" },
  { id: "style-pixel", label: "Pixel art", category: "style", engine: "global-restyle", maskMode: "full-frame", prompt: "restyle as retro pixel art" },
  { id: "style-realistic", label: "Realistic", category: "style", engine: "global-restyle", maskMode: "full-frame", prompt: "restyle stylized footage as photorealistic" },
  { id: "style-tokyo-night", label: "Tokyo night street", category: "style", engine: "global-restyle", maskMode: "full-frame", prompt: "turn this street into a tokyo street at night with neon signage" },

  /* ------------------------------- People ------------------------------ */
  { id: "person-replace", label: "Replace person", category: "people", engine: "masked-v2v", maskMode: "auto-subject", prompt: "replace the selected person with {prompt}, preserving pose, movement, expressions and lip sync" },
  { id: "person-astronaut", label: "→ Astronaut", category: "people", engine: "masked-v2v", maskMode: "auto-subject", prompt: "replace the selected person with an astronaut in a detailed spacesuit, preserving pose and motion" },
  { id: "person-robot", label: "→ Robot", category: "people", engine: "masked-v2v", maskMode: "auto-subject", prompt: "replace the selected person with a sleek humanoid robot, preserving pose and motion" },
  { id: "person-knight", label: "→ Knight", category: "people", engine: "masked-v2v", maskMode: "auto-subject", prompt: "replace the selected person with a medieval knight in armor, preserving pose and motion" },
  { id: "person-anime", label: "→ Anime character", category: "people", engine: "masked-v2v", maskMode: "auto-subject", prompt: "replace the selected person with an anime character, preserving pose and motion" },
  { id: "clothes-change", label: "Change outfit", category: "people", engine: "masked-v2v", maskMode: "auto-clothing", prompt: "change the outfit to {prompt}, preserving body motion and fit" },
  { id: "clothes-suit", label: "→ Black suit", category: "people", engine: "masked-v2v", maskMode: "auto-clothing", prompt: "change the outfit to a tailored black suit" },
  { id: "clothes-wedding", label: "→ Wedding dress", category: "people", engine: "masked-v2v", maskMode: "auto-clothing", prompt: "change the outfit to an elegant wedding dress" },
  { id: "clothes-spacesuit", label: "→ Space suit", category: "people", engine: "masked-v2v", maskMode: "auto-clothing", prompt: "change the outfit to a nasa-style space suit" },
  { id: "hair-change", label: "Change hairstyle", category: "people", engine: "masked-v2v", maskMode: "auto-hair", prompt: "change the hairstyle to {prompt}, preserving head motion" },
  { id: "hair-color", label: "Hair color", category: "people", engine: "masked-v2v", maskMode: "auto-hair", prompt: "change the hair color to {prompt}, keep natural texture" },
  { id: "hair-long", label: "→ Long hair", category: "people", engine: "masked-v2v", maskMode: "auto-hair", prompt: "change to long flowing hair" },
  { id: "hair-curly", label: "→ Curly", category: "people", engine: "masked-v2v", maskMode: "auto-hair", prompt: "change to curly hair" },
  { id: "hair-bald", label: "→ Bald", category: "people", engine: "masked-v2v", maskMode: "auto-hair", prompt: "make the person bald, realistic scalp" },
  { id: "makeup-natural", label: "Natural makeup", category: "people", engine: "masked-v2v", maskMode: "auto-face", prompt: "apply subtle natural makeup" },
  { id: "makeup-glam", label: "Glam makeup", category: "people", engine: "masked-v2v", maskMode: "auto-face", prompt: "apply glamorous evening makeup" },
  { id: "makeup-cyberpunk", label: "Cyberpunk makeup", category: "people", engine: "masked-v2v", maskMode: "auto-face", prompt: "apply neon cyberpunk face paint and makeup" },
  { id: "makeup-vampire", label: "Vampire", category: "people", engine: "masked-v2v", maskMode: "auto-face", prompt: "apply pale vampire makeup with subtle fangs" },
  { id: "face-beard", label: "Add beard", category: "people", engine: "masked-v2v", maskMode: "auto-face", prompt: "add a well-groomed beard, matched to hair color" },
  { id: "face-glasses", label: "Add glasses", category: "people", engine: "masked-v2v", maskMode: "auto-face", prompt: "add stylish glasses that track the face" },
  { id: "face-tattoo", label: "Add tattoo", category: "people", engine: "masked-v2v", maskMode: "painted", prompt: "add a tattoo of {prompt} on the selected skin area, tracking the body" },
  { id: "face-eyecolor", label: "Eye color", category: "people", engine: "masked-v2v", maskMode: "auto-face", prompt: "change the eye color to {prompt}, preserve blinks and gaze" },
  { id: "face-age-up", label: "Age +20 years", category: "people", engine: "masked-v2v", maskMode: "auto-face", prompt: "make the person look about 20 years older, preserving identity and expressions" },
  { id: "face-age-down", label: "Age −20 years", category: "people", engine: "masked-v2v", maskMode: "auto-face", prompt: "make the person look about 20 years younger, preserving identity and expressions" },
  { id: "face-smile", label: "Smile", category: "people", engine: "masked-v2v", maskMode: "auto-face", prompt: "make the person smile naturally, preserving identity" },

  /* ------------------------------ Enhance ------------------------------ */
  { id: "up-4k", label: "Upscale to 4K", category: "enhance", engine: "enhance", maskMode: "full-frame", prompt: "upscale to 4k with detail restoration" },
  { id: "up-8k", label: "Upscale to 8K", category: "enhance", engine: "enhance", maskMode: "full-frame", prompt: "upscale to 8k with detail restoration" },
  { id: "enh-sharpen", label: "Sharpen", category: "enhance", engine: "enhance", maskMode: "full-frame", prompt: "sharpen fine detail without halos" },
  { id: "enh-deblur", label: "Deblur", category: "enhance", engine: "enhance", maskMode: "full-frame", prompt: "remove motion blur and focus blur" },
  { id: "enh-denoise", label: "Denoise", category: "enhance", engine: "enhance", maskMode: "full-frame", prompt: "remove sensor noise while keeping texture" },
  { id: "enh-hdr", label: "HDR", category: "enhance", engine: "enhance", maskMode: "full-frame", prompt: "expand dynamic range, recover highlights and shadows" },
  { id: "enh-interp", label: "60fps smooth", category: "enhance", engine: "enhance", maskMode: "full-frame", prompt: "interpolate frames to smooth 60fps" },

  /* --------------------------- Motion & Camera -------------------------- */
  { id: "mo-slow", label: "Slow motion", category: "motion-camera", engine: "retime-camera", maskMode: "full-frame", prompt: "slow motion 0.5x with frame interpolation" },
  { id: "mo-ramp", label: "Speed ramp", category: "motion-camera", engine: "retime-camera", maskMode: "full-frame", prompt: "speed ramp: slow in the middle, fast at the ends" },
  { id: "mo-freeze", label: "Freeze frame", category: "motion-camera", engine: "retime-camera", maskMode: "full-frame", prompt: "freeze frame at the playhead for 1 second" },
  { id: "mo-reverse", label: "Reverse", category: "motion-camera", engine: "retime-camera", maskMode: "full-frame", prompt: "reverse the clip" },
  { id: "mo-boomerang", label: "Boomerang", category: "motion-camera", engine: "retime-camera", maskMode: "full-frame", prompt: "boomerang: play forward then backward seamlessly" },
  { id: "mo-loop", label: "Seamless loop", category: "motion-camera", engine: "retime-camera", maskMode: "full-frame", prompt: "make the clip loop seamlessly" },
  { id: "cam-stabilize", label: "Stabilize", category: "motion-camera", engine: "retime-camera", maskMode: "full-frame", prompt: "remove camera shake, handheld stabilization" },
  { id: "cam-pan", label: "Virtual pan", category: "motion-camera", engine: "retime-camera", maskMode: "full-frame", prompt: "add a slow virtual pan across the frame" },
  { id: "cam-zoom", label: "Virtual zoom", category: "motion-camera", engine: "retime-camera", maskMode: "full-frame", prompt: "add a slow cinematic push-in zoom" },
  { id: "cam-orbit", label: "Orbit", category: "motion-camera", engine: "retime-camera", maskMode: "full-frame", prompt: "simulate a subtle orbit around the subject" },

  /* -------------------------------- Text ------------------------------- */
  { id: "text-detect", label: "Detect text", category: "text", engine: "text-ops", maskMode: "auto-text", prompt: "detect all readable text in the video" },
  { id: "text-replace", label: "Replace text", category: "text", engine: "text-ops", maskMode: "auto-text", prompt: "replace the selected text with: {prompt}, matching font, color and perspective" },
  { id: "text-translate", label: "Translate text", category: "text", engine: "text-ops", maskMode: "auto-text", prompt: "translate the selected text to {prompt}, keep style" },
  { id: "text-remove", label: "Remove text", category: "text", engine: "text-ops", maskMode: "auto-text", prompt: "remove the selected text and restore the surface" },
  { id: "text-restyle", label: "Restyle text", category: "text", engine: "text-ops", maskMode: "auto-text", prompt: "restyle the selected text: {prompt}" },
];

/** The free-form "Magic prompt" entry — no preset, user describes anything. */
export const MAGIC_PROMPT_PRESET: EditPreset = {
  id: "magic",
  label: "Magic prompt",
  category: "transform",
  engine: "global-restyle",
  maskMode: "full-frame",
  prompt: "{prompt}",
};

export function presetsByCategory(categoryId: string): EditPreset[] {
  return EDIT_PRESETS.filter((p) => p.category === categoryId);
}

/** True when the preset needs the user to type something. */
export function needsPromptInput(preset: EditPreset): boolean {
  return preset.prompt.includes("{prompt}");
}

/** True when the preset expects a painted/selected mask. */
export function needsPaintedMask(preset: EditPreset): boolean {
  return preset.maskMode === "painted";
}

export function resolvePrompt(preset: EditPreset, userText: string): string {
  return preset.prompt.replaceAll("{prompt}", userText.trim());
}

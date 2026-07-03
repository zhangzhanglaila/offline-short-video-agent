/**
 * Theme System — Light/Dark palettes for video rendering.
 *
 * All color tokens live here. Components import a VideoTheme object
 * instead of hardcoding colors. Layout JSON can set `theme: "light" | "dark"`.
 */

export interface VideoTheme {
	/** Main background color */
	bg: string;
	/** Full CSS gradient for scene background */
	bgGradient: string;
	/** Card/node base fill */
	bgCard: string;

	/** Titles, hero labels */
	textPrimary: string;
	/** Summaries, captions */
	textSecondary: string;
	/** Inactive/ghost text */
	textMuted: string;

	/** Primary accent color */
	accent: string;
	/** Glow shadow rgba */
	accentGlow: string;
	/** Hero node fill */
	accentFill: string;

	/** Default node border */
	nodeBorder: string;
	/** Default node fill */
	nodeFill: string;
	/** Node label text */
	nodeText: string;
	/** Node role subtext */
	nodeRoleText: string;
	/** Hero-tier border */
	heroBorder: string;
	/** Hero-tier fill */
	heroFill: string;
	/** Hero-tier text */
	heroText: string;

	/** Default edge stroke */
	edgeStroke: string;
	/** Background ghost stroke */
	edgeGhost: string;
	/** Edge label text */
	edgeLabel: string;
	/** Edge label halo stroke */
	edgeLabelStroke: string;

	/** Active glow inset shadow */
	glowInset: string;
	/** Inactive inset shadow */
	inactiveInset: string;
	/** Miss-effect red */
	missRed: string;

	/** Debug overlay background */
	debugBg: string;
	/** Debug overlay text */
	debugText: string;

	/** Card scene: card border colors (4 rotating) */
	cardBorders: string[];
	/** Card scene: card gradient fills (4 rotating) */
	cardGradients: string[];
	/** Card scene: card text color */
	cardText: string;

	/** Hook scene: accent line gradient */
	hookAccentLine: string;
}

export const darkTheme: VideoTheme = {
	bg: "#071018",
	bgGradient:
		"linear-gradient(135deg, rgba(33,150,243,0.18) 0%, transparent 34%), linear-gradient(35deg, rgba(255,111,97,0.14) 0%, transparent 30%), linear-gradient(180deg, #071018 0%, #0b111a 54%, #111827 100%)",
	bgCard: "rgba(13,24,38,0.74)",

	textPrimary: "#f8fbff",
	textSecondary: "rgba(221,235,255,0.68)",
	textMuted: "rgba(222,235,255,0.62)",

	accent: "#4cc9f0",
	accentGlow: "rgba(76,201,240,0.34)",
	accentFill: "rgba(76,201,240,0.16)",

	nodeBorder: "#90b4ff",
	nodeFill: "rgba(17,30,48,0.78)",
	nodeText: "#eef6ff",
	nodeRoleText: "rgba(238,246,255,0.58)",
	heroBorder: "#ffb86b",
	heroFill: "rgba(255,184,107,0.17)",
	heroText: "#f8fbff",

	edgeStroke: "#8bd3ff",
	edgeGhost: "rgba(159,182,212,0.22)",
	edgeLabel: "#f8fbff",
	edgeLabelStroke: "#070b10",

	glowInset: "rgba(255,255,255,0.06)",
	inactiveInset: "rgba(255,255,255,0.04)",
	missRed: "rgba(255, 72, 72, ",  // prefix — alpha appended dynamically

	debugBg: "rgba(0,0,0,0.72)",
	debugText: "#0f0",

	cardBorders: [
		"rgba(76,201,240,0.45)",
		"rgba(255,184,107,0.42)",
		"rgba(126,231,135,0.38)",
		"rgba(255,111,145,0.38)",
	],
	cardGradients: [
		"linear-gradient(135deg, rgba(76,201,240,0.20), rgba(35,86,145,0.10))",
		"linear-gradient(135deg, rgba(255,184,107,0.18), rgba(255,111,97,0.08))",
		"linear-gradient(135deg, rgba(126,231,135,0.16), rgba(35,134,99,0.08))",
		"linear-gradient(135deg, rgba(255,111,145,0.16), rgba(123,92,255,0.08))",
	],
	cardText: "#eef6ff",

	hookAccentLine: "linear-gradient(90deg, transparent, rgba(76,201,240,0.72), rgba(255,184,107,0.72), transparent)",
};

export const lightTheme: VideoTheme = {
	bg: "#f8f9fa",
	bgGradient:
		"linear-gradient(135deg, rgba(37,99,235,0.11) 0%, transparent 34%), linear-gradient(35deg, rgba(245,158,11,0.12) 0%, transparent 30%), linear-gradient(180deg, #f8fafc 0%, #eef2f7 56%, #f8fafc 100%)",
	bgCard: "rgba(255,255,255,0.72)",

	textPrimary: "#1a1a2e",
	textSecondary: "#4a4a6a",
	textMuted: "#6b7280",

	accent: "#2563eb",
	accentGlow: "rgba(37,99,235,0.25)",
	accentFill: "rgba(37,99,235,0.10)",

	nodeBorder: "#93b4f5",
	nodeFill: "rgba(37,99,235,0.06)",
	nodeText: "#1a1a2e",
	nodeRoleText: "rgba(26,26,46,0.55)",
	heroBorder: "#2563eb",
	heroFill: "rgba(37,99,235,0.10)",
	heroText: "#1a1a2e",

	edgeStroke: "#6b8cce",
	edgeGhost: "rgba(107,140,206,0.15)",
	edgeLabel: "#1a1a2e",
	edgeLabelStroke: "#f8f9fa",

	glowInset: "rgba(37,99,235,0.08)",
	inactiveInset: "rgba(37,99,235,0.03)",
	missRed: "rgba(220, 38, 38, ",

	debugBg: "rgba(255,255,255,0.9)",
	debugText: "#1a1a2e",

	cardBorders: [
		"rgba(37,99,235,0.35)",
		"rgba(79,70,229,0.30)",
		"rgba(16,185,129,0.30)",
		"rgba(245,158,11,0.30)",
	],
	cardGradients: [
		"linear-gradient(135deg, rgba(37,99,235,0.10), rgba(59,130,246,0.05))",
		"linear-gradient(135deg, rgba(79,70,229,0.10), rgba(99,102,241,0.05))",
		"linear-gradient(135deg, rgba(16,185,129,0.10), rgba(52,211,153,0.05))",
		"linear-gradient(135deg, rgba(245,158,11,0.10), rgba(251,191,36,0.05))",
	],
	cardText: "#1a1a2e",

	hookAccentLine: "linear-gradient(90deg, transparent, rgba(37,99,235,0.5), transparent)",
};

export function getTheme(name?: "light" | "dark"): VideoTheme {
	return name === "dark" ? darkTheme : lightTheme;
}

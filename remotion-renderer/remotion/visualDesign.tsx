import React from "react";
import {Easing, interpolate} from "remotion";
import {FONT_FAMILY} from "./constants";
import type {VideoTheme} from "./theme";

export const clamp = (value: number, min: number, max: number) =>
	Math.max(min, Math.min(max, value));

export const fitFontSize = (text: string, base: number, maxChars: number) => {
	const length = Array.from(text || "").length;
	if (length <= maxChars) return base;
	const ratio = maxChars / Math.max(length, 1);
	return Math.round(clamp(base * (0.78 + ratio * 0.22), base * 0.68, base));
};

export const readableShadow = (theme: VideoTheme, strength = 1) =>
	`0 2px 18px ${theme.edgeLabelStroke}AA, 0 0 ${Math.round(24 * strength)}px ${theme.accentGlow}`;

export const panelStyle = (theme: VideoTheme, opacity = 0.9): React.CSSProperties => ({
	background: `linear-gradient(180deg, ${theme.bgCard}, rgba(255,255,255,${theme.bg === "#071018" ? 0.04 : 0.68}))`,
	border: `1px solid ${theme.nodeBorder}55`,
	boxShadow: `0 18px 54px rgba(0,0,0,${theme.bg === "#071018" ? 0.32 : 0.12}), inset 0 1px 0 rgba(255,255,255,${opacity * 0.32})`,
	backdropFilter: "blur(10px)",
});

export const SceneBackdrop: React.FC<{
	theme: VideoTheme;
	frame: number;
	width?: number;
	height?: number;
	children?: React.ReactNode;
}> = ({theme, frame, children}) => {
	const drift = interpolate(Math.sin(frame * 0.012), [-1, 1], [-18, 18], {
		easing: Easing.inOut(Easing.cubic),
	});
	const isDark = theme.bg === "#071018";

	return (
		<div
			style={{
				position: "absolute",
				inset: 0,
				overflow: "hidden",
				background: theme.bgGradient,
				fontFamily: FONT_FAMILY,
			}}
		>
			<div
				style={{
					position: "absolute",
					inset: 0,
					backgroundImage: `
						linear-gradient(120deg, rgba(255,255,255,${isDark ? 0.055 : 0.34}) 0 1px, transparent 1px 100%),
						linear-gradient(180deg, rgba(255,255,255,${isDark ? 0.035 : 0.22}) 0 1px, transparent 1px 100%)
					`,
					backgroundSize: "72px 72px, 72px 72px",
					transform: `translate3d(${drift}px, ${drift * -0.6}px, 0)`,
					opacity: isDark ? 0.22 : 0.28,
				}}
			/>
			<div
				style={{
					position: "absolute",
					inset: 0,
					background: isDark
						? "linear-gradient(180deg, rgba(255,255,255,0.07), transparent 22%, transparent 72%, rgba(0,0,0,0.42)), radial-gradient(ellipse at center, transparent 42%, rgba(0,0,0,0.48) 100%)"
						: "linear-gradient(180deg, rgba(255,255,255,0.74), transparent 30%, rgba(17,24,39,0.05)), radial-gradient(ellipse at center, transparent 46%, rgba(15,23,42,0.13) 100%)",
					pointerEvents: "none",
				}}
			/>
			{children}
		</div>
	);
};

export const CaptionPlate: React.FC<{
	text: React.ReactNode;
	theme: VideoTheme;
	style?: React.CSSProperties;
}> = ({text, theme, style}) => (
	<div
		style={{
			...panelStyle(theme, 0.85),
			position: "absolute",
			left: 96,
			right: 96,
			bottom: 190,
			minHeight: 86,
			borderRadius: 8,
			padding: "22px 32px",
			display: "flex",
			alignItems: "center",
			justifyContent: "center",
			color: theme.textPrimary,
			fontSize: 34,
			fontWeight: 760,
			lineHeight: 1.28,
			textAlign: "center",
			textShadow: readableShadow(theme, 0.55),
			zIndex: 20,
			...style,
		}}
	>
		{text}
	</div>
);

const hashString = (value: string) => {
	let hash = 0;
	for (let index = 0; index < value.length; index++) {
		hash = (hash * 31 + value.charCodeAt(index)) | 0;
	}
	return Math.abs(hash);
};

export const ConceptIllustration: React.FC<{
	label: string;
	theme: VideoTheme;
	frame: number;
	variant?: "hero" | "graph" | "cards";
	motif?: "data" | "flow" | "insight";
	style?: React.CSSProperties;
}> = ({label, theme, frame, variant = "hero", motif, style}) => {
	const seed = hashString(label || "concept");
	const spin = frame * 0.012 + (seed % 90);
	const bob = Math.sin(frame * 0.04 + seed) * 10;
	const pulse = 0.82 + Math.sin(frame * 0.055 + seed) * 0.18;
	const accentA = theme.accent;
	const accentB = theme.heroBorder;
	const accentC = theme.cardBorders[(seed + 2) % theme.cardBorders.length] ?? theme.accent;
	const compact = variant !== "hero";
	const size = variant === "hero" ? 270 : variant === "graph" ? 180 : 210;
	const coreY = compact ? 158 : 210;
	const resolvedMotif =
		motif ?? (variant === "graph" ? "flow" : variant === "cards" ? "insight" : "data");

	return (
		<div
			style={{
				position: "absolute",
				width: size,
				height: size,
				transform: `translateY(${bob}px)`,
				filter: "drop-shadow(0 28px 54px rgba(0,0,0,0.32))",
				pointerEvents: "none",
				zIndex: variant === "graph" ? 1 : 4,
				...style,
			}}
		>
			<svg width="100%" height="100%" viewBox="0 0 520 520">
				<defs>
					<radialGradient id={`halo-${seed}`} cx="50%" cy="50%" r="50%">
						<stop offset="0%" stopColor={accentA} stopOpacity="0.38" />
						<stop offset="58%" stopColor={accentB} stopOpacity="0.12" />
						<stop offset="100%" stopColor="#000" stopOpacity="0" />
					</radialGradient>
					<linearGradient id={`panel-${seed}`} x1="0" x2="1" y1="0" y2="1">
						<stop offset="0%" stopColor="rgba(255,255,255,0.26)" />
						<stop offset="45%" stopColor={theme.bgCard} />
						<stop offset="100%" stopColor="rgba(255,255,255,0.08)" />
					</linearGradient>
					<linearGradient id={`wire-${seed}`} x1="0" x2="1">
						<stop offset="0%" stopColor={accentA} stopOpacity="0.1" />
						<stop offset="45%" stopColor={accentA} stopOpacity="0.9" />
						<stop offset="100%" stopColor={accentB} stopOpacity="0.12" />
					</linearGradient>
					<filter id={`softGlow-${seed}`} x="-40%" y="-40%" width="180%" height="180%">
						<feGaussianBlur stdDeviation="8" result="blur" />
						<feMerge>
							<feMergeNode in="blur" />
							<feMergeNode in="SourceGraphic" />
						</feMerge>
					</filter>
				</defs>

				<circle cx="260" cy="260" r={compact ? 180 : 220} fill={`url(#halo-${seed})`} opacity={0.86} />
				<g transform={`rotate(${spin} 260 260)`} opacity="0.48">
					<circle cx="260" cy="260" r="188" fill="none" stroke={accentA} strokeWidth="2" strokeDasharray="18 22" />
					<circle cx="260" cy="260" r="132" fill="none" stroke={accentB} strokeWidth="1.5" strokeDasharray="10 16" />
				</g>

				<g filter={`url(#softGlow-${seed})`}>
					<path
						d="M112 324 C170 252, 206 250, 260 302 S368 354, 420 270"
						fill="none"
						stroke={`url(#wire-${seed})`}
						strokeWidth="10"
						strokeLinecap="round"
						opacity="0.72"
					/>
					<path
						d="M132 220 C190 168, 248 178, 294 220 S368 282, 424 210"
						fill="none"
						stroke={accentC}
						strokeWidth="5"
						strokeLinecap="round"
						opacity="0.45"
					/>
				</g>

				{resolvedMotif === "data" ? (
					<>
						<g transform={`translate(0 ${Math.sin(frame * 0.035) * 6})`}>
							<rect x="132" y="178" width="256" height="168" rx="18" fill={`url(#panel-${seed})`} stroke="rgba(255,255,255,0.26)" />
							<rect x="154" y="202" width="112" height="18" rx="9" fill={accentA} opacity={0.72 * pulse} />
							<rect x="154" y="236" width="184" height="13" rx="7" fill="rgba(255,255,255,0.55)" opacity="0.72" />
							<rect x="154" y="265" width="148" height="13" rx="7" fill="rgba(255,255,255,0.34)" />
							<rect x="154" y="294" width="198" height="13" rx="7" fill={accentB} opacity="0.42" />
							<circle cx="344" cy="216" r="24" fill={accentB} opacity={0.84} />
							<path d="M332 216 L342 226 L360 204" fill="none" stroke="#fff" strokeWidth="7" strokeLinecap="round" strokeLinejoin="round" />
						</g>
						<g transform={`translate(${Math.sin(frame * 0.031 + 1) * 8} 0)`}>
							<ellipse cx="260" cy={coreY + 170} rx="84" ry="24" fill={accentA} opacity="0.23" />
							<path d={`M176 ${coreY + 88} C176 ${coreY + 56}, 344 ${coreY + 56}, 344 ${coreY + 88} L344 ${coreY + 154} C344 ${coreY + 188}, 176 ${coreY + 188}, 176 ${coreY + 154} Z`} fill="rgba(8,16,28,0.72)" stroke={accentA} strokeWidth="3" />
							<ellipse cx="260" cy={coreY + 88} rx="84" ry="32" fill="rgba(255,255,255,0.12)" stroke={accentA} strokeWidth="3" />
							<path d={`M178 ${coreY + 122} C202 ${coreY + 148}, 318 ${coreY + 148}, 342 ${coreY + 122}`} fill="none" stroke={accentB} strokeWidth="3" opacity="0.72" />
						</g>
					</>
				) : null}

				{resolvedMotif === "flow" ? (
					<g transform={`translate(0 ${Math.sin(frame * 0.034) * 7})`}>
						<rect x="108" y="176" width="116" height="88" rx="18" fill={`url(#panel-${seed})`} stroke={accentA} strokeWidth="3" />
						<rect x="202" y="292" width="126" height="88" rx="18" fill="rgba(8,16,28,0.78)" stroke={accentB} strokeWidth="3" />
						<rect x="308" y="170" width="118" height="92" rx="18" fill={`url(#panel-${seed})`} stroke={accentC} strokeWidth="3" />
						<path d="M218 220 C262 214, 284 214, 322 218" fill="none" stroke={accentA} strokeWidth="8" strokeLinecap="round" opacity={0.66 * pulse} />
						<path d="M310 262 C300 290, 286 302, 266 318" fill="none" stroke={accentB} strokeWidth="8" strokeLinecap="round" opacity="0.66" />
						<path d="M218 264 C228 292, 244 306, 264 318" fill="none" stroke={accentC} strokeWidth="6" strokeLinecap="round" opacity="0.54" />
						<circle cx="166" cy="220" r="24" fill={accentA} opacity="0.24" />
						<path d="M150 220 H182 M166 204 V236" stroke={accentA} strokeWidth="7" strokeLinecap="round" />
						<path d="M244 334 L264 308 L286 334 L268 334 L268 358 L252 358 L252 334 Z" fill={accentB} opacity="0.84" />
						<rect x="330" y="196" width="72" height="12" rx="6" fill={accentC} opacity="0.72" />
						<rect x="330" y="222" width="50" height="12" rx="6" fill="rgba(255,255,255,0.52)" />
						{[0, 1, 2].map((i) => (
							<circle
								key={i}
								cx={196 + i * 62 + Math.sin(frame * 0.065 + i) * 10}
								cy={268 + Math.cos(frame * 0.05 + i) * 18}
								r="8"
								fill={i === 1 ? accentB : accentA}
								opacity="0.76"
							/>
						))}
					</g>
				) : null}

				{resolvedMotif === "insight" ? (
					<g transform={`translate(${Math.sin(frame * 0.03 + 2) * 7} ${Math.cos(frame * 0.026) * 6})`}>
						<path d="M158 168 H332 L386 224 V366 H158 Z" fill={`url(#panel-${seed})`} stroke="rgba(255,255,255,0.28)" strokeWidth="2" />
						<path d="M332 168 V224 H386" fill="rgba(255,255,255,0.18)" stroke={accentB} strokeWidth="2" />
						<path d="M194 314 C224 280, 244 292, 266 260 S318 240, 348 202" fill="none" stroke={accentA} strokeWidth="9" strokeLinecap="round" opacity={0.68 * pulse} />
						<circle cx="198" cy="312" r="12" fill={accentA} />
						<circle cx="266" cy="260" r="12" fill={accentB} />
						<circle cx="348" cy="202" r="12" fill={accentC} />
						<rect x="194" y="338" width="138" height="13" rx="7" fill="rgba(255,255,255,0.42)" />
						<rect x="194" y="360" width="94" height="13" rx="7" fill={accentB} opacity="0.52" />
						<g transform={`rotate(${Math.sin(frame * 0.04) * 4} 252 226)`}>
							<circle cx="252" cy="226" r="42" fill="rgba(8,16,28,0.78)" stroke={accentB} strokeWidth="4" />
							<path d="M252 190 C230 214, 230 234, 252 260 C274 234, 274 214, 252 190 Z" fill={accentB} opacity="0.78" />
							<path d="M230 226 H274" stroke="#fff" strokeWidth="5" strokeLinecap="round" opacity="0.8" />
						</g>
					</g>
				) : null}

				{[0, 1, 2, 3].map((i) => {
					const angle = spin * 0.7 + i * Math.PI / 2;
					const x = 260 + Math.cos(angle) * (compact ? 150 : 188);
					const y = 260 + Math.sin(angle) * (compact ? 118 : 152);
					return (
						<g key={i}>
							<circle cx={x} cy={y} r={18 + (i % 2) * 5} fill={i % 2 ? accentB : accentA} opacity="0.88" />
							<circle cx={x} cy={y} r={30 + (i % 2) * 6} fill="none" stroke={i % 2 ? accentB : accentA} strokeWidth="2" opacity="0.32" />
						</g>
					);
				})}
			</svg>
		</div>
	);
};

import React from "react";
import {AbsoluteFill, Easing, interpolate, useCurrentFrame} from "remotion";
import {FONT_FAMILY} from "./constants";
import type {VideoTheme} from "./theme";

interface HookSceneProps {
	text: string;
	durationInFrames: number;
	theme: VideoTheme;
}

export const HookScene: React.FC<HookSceneProps> = ({text, durationInFrames, theme}) => {
	const frame = useCurrentFrame();

	const fadeIn = interpolate(frame, [0, 15], [0, 1], {
		extrapolateLeft: "clamp",
		extrapolateRight: "clamp",
	});
	const fadeOut = interpolate(frame, [durationInFrames - 20, durationInFrames], [1, 0], {
		extrapolateLeft: "clamp",
		extrapolateRight: "clamp",
	});
	const scale = interpolate(frame, [0, 40], [1.08, 1], {
		easing: Easing.out(Easing.cubic),
		extrapolateLeft: "clamp",
		extrapolateRight: "clamp",
	});
	const bgPulse = 1 + Math.sin(frame * 0.06) * 0.04;

	return (
		<AbsoluteFill
			style={{
				background: theme.bgGradient,
				fontFamily: FONT_FAMILY,
			}}
		>
			{/* Ambient glow behind text */}
			<div
				style={{
					position: "absolute",
					inset: 0,
					background: `radial-gradient(ellipse 60% 30% at 50% 45%, ${theme.accentFill.replace("0.16", (0.12 * bgPulse).toFixed(2))}, transparent 70%)`,
				}}
			/>
			<div
				style={{
					position: "absolute",
					inset: 0,
					display: "flex",
					flexDirection: "column",
					alignItems: "center",
					justifyContent: "center",
					opacity: fadeIn * fadeOut,
					transform: `scale(${scale})`,
				}}
			>
				<div
					style={{
						color: theme.textPrimary,
						fontSize: 68,
						fontWeight: 860,
						textAlign: "center",
						textShadow: `0 0 48px ${theme.accentGlow}, 0 4px 24px ${theme.edgeLabelStroke}80`,
						maxWidth: 800,
						lineHeight: 1.2,
						padding: "0 40px",
					}}
				>
					{text}
				</div>
				<div
					style={{
						marginTop: 32,
						width: 120,
						height: 3,
						background: theme.hookAccentLine,
						borderRadius: 2,
					}}
				/>
			</div>
		</AbsoluteFill>
	);
};

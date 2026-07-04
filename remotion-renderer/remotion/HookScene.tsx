import React from "react";
import {AbsoluteFill, Easing, interpolate, useCurrentFrame} from "remotion";
import {FONT_FAMILY} from "./constants";
import type {VideoTheme} from "./theme";
import {ConceptIllustration, SceneBackdrop, fitFontSize, readableShadow} from "./visualDesign";

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
	const fontSize = fitFontSize(text, 70, 22);

	return (
		<AbsoluteFill style={{fontFamily: FONT_FAMILY}}>
			<SceneBackdrop theme={theme} frame={frame}>
			<div
				style={{
					position: "absolute",
					inset: 0,
					background: `linear-gradient(110deg, transparent 18%, ${theme.accentFill.replace("0.16", (0.10 * bgPulse).toFixed(2))} 48%, transparent 78%)`,
					opacity: 0.78,
				}}
			/>
			<div
				style={{
					position: "absolute",
					left: 78,
					right: 78,
					top: 460,
					height: 720,
					opacity: fadeIn * fadeOut,
					transform: `scale(${scale})`,
				}}
			>
				<ConceptIllustration
					label={text}
					theme={theme}
					frame={frame}
					variant="hero"
					motif="data"
					style={{
						right: 28,
						top: 162,
						opacity: 0.88,
					}}
				/>
				<div
					style={{
						position: "absolute",
						left: 0,
						top: 168,
						width: 640,
						zIndex: 6,
						color: theme.textPrimary,
						fontSize: Math.min(fontSize, 62),
						fontWeight: 860,
						textAlign: "left",
						textShadow: readableShadow(theme, 1.25),
						lineHeight: 1.08,
					}}
				>
					{text}
				</div>
				<div
					style={{
						position: "absolute",
						left: 0,
						top: 168 + Math.min(fontSize, 62) * 2.4,
						width: 168,
						height: 3,
						zIndex: 6,
						background: theme.hookAccentLine,
						borderRadius: 2,
					}}
				/>
			</div>
			</SceneBackdrop>
		</AbsoluteFill>
	);
};

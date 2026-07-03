import React from "react";
import {AbsoluteFill, Easing, interpolate, spring, useCurrentFrame, useVideoConfig} from "remotion";
import {FONT_FAMILY} from "./constants";
import type {VideoTheme} from "./theme";
import {ConceptIllustration, SceneBackdrop, fitFontSize, panelStyle, readableShadow} from "./visualDesign";

interface CardSceneProps {
	title: string;
	items: string[];
	durationInFrames: number;
	theme: VideoTheme;
}

export const CardScene: React.FC<CardSceneProps> = ({title, items, durationInFrames, theme}) => {
	const frame = useCurrentFrame();
	const {fps} = useVideoConfig();

	const fadeIn = interpolate(frame, [0, 12], [0, 1], {
		extrapolateLeft: "clamp",
		extrapolateRight: "clamp",
	});
	const fadeOut = interpolate(frame, [durationInFrames - 18, durationInFrames], [1, 0], {
		extrapolateLeft: "clamp",
		extrapolateRight: "clamp",
	});

	const titleAppear = spring({
		frame: frame - 5,
		fps,
		config: {damping: 14, stiffness: 100, mass: 0.8},
	});

	return (
		<AbsoluteFill style={{fontFamily: FONT_FAMILY}}>
			<SceneBackdrop theme={theme} frame={frame}>
			<ConceptIllustration
				label={title || items.join("|")}
				theme={theme}
				frame={frame}
				variant="cards"
				motif="insight"
				style={{
					left: 78,
					top: 330,
					opacity: 0.34,
					zIndex: 1,
					transform: `translateY(${Math.sin(frame * 0.026) * 8}px) rotate(-5deg)`,
				}}
			/>
			<ConceptIllustration
				label={`${title}-summary`}
				theme={theme}
				frame={frame + 80}
				variant="cards"
				motif="data"
				style={{
					right: 68,
					bottom: 360,
					opacity: 0.26,
					zIndex: 1,
					transform: `translateY(${Math.cos(frame * 0.023) * 8}px) rotate(6deg) scale(0.82)`,
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
					padding: "0 60px",
					zIndex: 5,
				}}
			>
				<div
					style={{
						color: theme.textPrimary,
						fontSize: fitFontSize(title, 44, 18),
						fontWeight: 800,
						textAlign: "center",
						textShadow: readableShadow(theme, 0.75),
						marginBottom: 48,
						transform: `translateY(${interpolate(titleAppear, [0, 1], [-20, 0])}px)`,
						opacity: titleAppear,
					}}
				>
					{title}
				</div>
				<div style={{display: "flex", flexWrap: "wrap", justifyContent: "center", gap: 18, maxWidth: 900}}>
					{items.map((item, i) => {
						const cardSpring = spring({
							frame: frame - 15 - i * 10,
							fps,
							config: {damping: 15, stiffness: 90, mass: 0.85},
						});
						const colors = {gradient: theme.cardGradients[i % theme.cardGradients.length], border: theme.cardBorders[i % theme.cardBorders.length]};
						return (
							<div
								key={i}
								style={{
									...panelStyle(theme, 0.78),
									width: items.length <= 3 ? 300 : 268,
									height: 142,
									borderRadius: 8,
									border: `1px solid ${colors.border}`,
									background: colors.gradient,
									display: "flex",
									alignItems: "center",
									justifyContent: "center",
									opacity: cardSpring,
									transform: `translateY(${interpolate(cardSpring, [0, 1], [36, 0])}px) scale(${interpolate(cardSpring, [0, 1], [0.92, 1])})`,
									boxShadow: `0 18px ${34 * cardSpring}px rgba(0,0,0,0.24), 0 0 ${18 * cardSpring}px ${theme.accentGlow}`,
								}}
							>
								<span
									style={{
										color: theme.cardText,
										fontSize: fitFontSize(item, 27, 12),
										fontWeight: 760,
										textAlign: "center",
										lineHeight: 1.18,
										padding: "0 18px",
										textShadow: readableShadow(theme, 0.35),
										wordBreak: "break-word",
									}}
								>
									{item}
								</span>
							</div>
						);
					})}
				</div>
			</div>
			</SceneBackdrop>
		</AbsoluteFill>
	);
};

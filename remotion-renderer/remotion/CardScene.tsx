import React from "react";
import {AbsoluteFill, Easing, interpolate, spring, useCurrentFrame, useVideoConfig} from "remotion";
import {FONT_FAMILY} from "./constants";
import type {VideoTheme} from "./theme";

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
		<AbsoluteFill
			style={{
				background: theme.bgGradient,
				fontFamily: FONT_FAMILY,
			}}
		>
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
				}}
			>
				<div
					style={{
						color: "#f8fbff",
						fontSize: 44,
						fontWeight: 800,
						textAlign: "center",
						textShadow: `0 0 24px ${theme.accentGlow}`,
						marginBottom: 48,
						transform: `translateY(${interpolate(titleAppear, [0, 1], [-20, 0])}px)`,
						opacity: titleAppear,
					}}
				>
					{title}
				</div>
				<div style={{display: "flex", flexWrap: "wrap", justifyContent: "center", gap: 20, maxWidth: 900}}>
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
									width: 260,
									height: 140,
									borderRadius: 20,
									border: `2px solid ${colors.border}`,
									background: colors.gradient,
									display: "flex",
									alignItems: "center",
									justifyContent: "center",
									opacity: cardSpring,
									transform: `translateY(${interpolate(cardSpring, [0, 1], [36, 0])}px) scale(${interpolate(cardSpring, [0, 1], [0.92, 1])})`,
									boxShadow: `0 0 ${20 * cardSpring}px ${theme.accentGlow}`,
								}}
							>
								<span
									style={{
										color: theme.cardText,
										fontSize: 28,
										fontWeight: 700,
										textAlign: "center",
										padding: "0 16px",
									}}
								>
									{item}
								</span>
							</div>
						);
					})}
				</div>
			</div>
		</AbsoluteFill>
	);
};

import React from "react";
import {interpolate, spring, useVideoConfig} from "remotion";
import {FONT_FAMILY} from "../constants";
import type {VideoTheme} from "../theme";
import type {GraphNode} from "../types";
import {fitFontSize, panelStyle, readableShadow} from "../visualDesign";

type NodeTier = "hero" | "secondary" | "other";

interface NodeRevealProps {
	node: GraphNode;
	index: number;
	active: boolean;
	visible: boolean;
	intensity: number;
	frame: number;
	missEffect?: boolean;
	tier?: NodeTier;
	emphasized?: boolean;
	theme: VideoTheme;
}

const tierStyles: Record<NodeTier, {glowMulti: number; scaleBump: number; fontSize: number; zBase: number; opacityBase: number}> = {
	hero:      {glowMulti: 1.4, scaleBump: 1.035, fontSize: 30, zBase: 10, opacityBase: 1},
	secondary: {glowMulti: 0.95, scaleBump: 1.015, fontSize: 25, zBase: 6,  opacityBase: 0.92},
	other:     {glowMulti: 0.48, scaleBump: 1.0,  fontSize: 21, zBase: 4,  opacityBase: 0.72},
};

export const NodeReveal: React.FC<NodeRevealProps> = ({
	node,
	index,
	active,
	visible,
	intensity,
	frame,
	missEffect = false,
	tier = "secondary",
	emphasized = false,
	theme,
}) => {
	const {fps} = useVideoConfig();
	if (!visible) return null;
	const heroColor = tier === "hero" ? theme.heroBorder : (node.color ?? theme.nodeBorder);
	const ts = tierStyles[tier];
	const labelFont = fitFontSize(node.label, ts.fontSize, tier === "hero" ? 10 : 12);
	const appear = spring({
		frame: frame - index * 6,
		fps,
		config: {damping: 16, stiffness: 95, mass: 0.9},
	});
	const pulse = active
		? 1 + Math.sin(frame * 0.13) * 0.025 * intensity * ts.glowMulti
		: 1;
	const activeGlow = active
		? 0.9 + Math.sin(frame * 0.09) * 0.1 * intensity * ts.glowMulti + (emphasized ? 0.35 : 0)
		: 0.2;
	const shakeX = missEffect ? Math.sin(frame * 0.5) * 8 : 0;
	const borderColor = missEffect
		? `${theme.missRed}${0.6 + Math.sin(frame * 0.7) * 0.4})`
		: heroColor;

	return (
		<div
			style={{
				position: "absolute",
				left: node.x,
				top: node.y,
				width: node.width,
				height: node.height,
				...panelStyle(theme, tier === "hero" ? 0.95 : 0.78),
				border: tier === "hero"
					? `2px solid ${borderColor}`
					: `1px solid ${borderColor}99`,
				borderRadius: 8,
				background: tier === "hero"
					? theme.heroFill
					: (node.fill ?? "rgba(155,183,255,0.12)"),
				boxShadow: active
					? `0 20px ${34 * ts.glowMulti * (emphasized ? 1.35 : 1)}px rgba(0,0,0,0.28), 0 0 ${26 * ts.glowMulti}px ${heroColor}55, inset 0 1px 0 rgba(255,255,255,0.24)`
					: `0 14px 30px rgba(0,0,0,0.18), inset 0 1px 0 rgba(255,255,255,0.18)`,
				opacity: interpolate(appear, [0, 1], [0, ts.opacityBase]),
				transform: `translateX(${shakeX}px) translateY(${interpolate(appear, [0, 1], [34, 0])}px) scale(${interpolate(appear, [0, 1], [0.88, 1]) * pulse * ts.scaleBump * (emphasized ? 1.15 : 1)})`,
				transformOrigin: "center center",
				display: "flex",
				alignItems: "center",
				justifyContent: "center",
				padding: "0 16px",
				color: tier === "hero" ? theme.heroText : theme.nodeText,
				fontFamily: FONT_FAMILY,
				fontSize: labelFont,
				fontWeight: tier === "hero" ? 820 : (tier === "secondary" ? 760 : 680),
				textAlign: "center",
				letterSpacing: 0,
				textShadow: active ? readableShadow(theme, 0.4) : "none",
				zIndex: active ? ts.zBase + 3 : ts.zBase,
			}}
		>
			<div>
				<div>{node.label}</div>
				{node.role ? (
					<div
						style={{
							marginTop: 8,
							fontSize: tier === "hero" ? 16 : (tier === "secondary" ? 15 : 13),
							fontWeight: 600,
							color: tier === "hero" ? theme.accent : theme.nodeRoleText,
							letterSpacing: 0,
						}}
					>
						{node.role}
					</div>
				) : null}
			</div>
		</div>
	);
};

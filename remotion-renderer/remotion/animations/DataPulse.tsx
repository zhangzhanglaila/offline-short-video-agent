import React from "react";
import {interpolate} from "remotion";
import type {GraphNode} from "../types";
import type {VideoTheme} from "../theme";

const clamp01 = (value: number) => Math.max(0, Math.min(1, value));

interface DataPulseProps {
	node: GraphNode;
	progress: number;
	intensity: number;
	theme: VideoTheme;
}

export const DataPulse: React.FC<DataPulseProps> = ({
	node,
	progress,
	intensity,
	theme,
}) => {
	const cx = node.x + node.width / 2;
	const cy = node.y + node.height / 2;
	const color = node.color ?? theme.edgeStroke;

	const rings = [0, 0.28, 0.56].map((offset) => {
		const ringProgress = clamp01((progress - offset) / 0.44);
		const radius = interpolate(ringProgress, [0, 1], [50, 220]);
		const opacity = interpolate(ringProgress, [0, 0.5, 1], [0.7, 0.25, 0]) * intensity;
		const strokeWidth = interpolate(ringProgress, [0, 1], [4, 1]);
		return {radius, opacity, strokeWidth};
	});

	return (
		<svg
			style={{
				position: "absolute",
				inset: 0,
				zIndex: 9,
				pointerEvents: "none",
				overflow: "visible",
			}}
		>
			{rings.map((ring, i) => (
				<circle
					key={i}
					cx={cx}
					cy={cy}
					r={ring.radius}
					fill="none"
					stroke={color}
					strokeWidth={ring.strokeWidth}
					opacity={ring.opacity}
				/>
			))}
		</svg>
	);
};

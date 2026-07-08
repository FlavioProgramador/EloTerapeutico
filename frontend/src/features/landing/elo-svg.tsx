"use client";

import { motion, useReducedMotion } from "framer-motion";
import { cn } from "@/lib/utils";

interface EloSvgProps {
  className?: string;
  size?: "hero" | "divider" | "compact";
}

export function EloSvg({ className, size = "hero" }: EloSvgProps) {
  const reduceMotion = useReducedMotion();

  const dims = {
    hero: { width: 480, height: 200, viewBox: "0 0 480 200" },
    divider: { width: 320, height: 60, viewBox: "0 0 320 60" },
    compact: { width: 160, height: 80, viewBox: "0 0 160 80" },
  }[size];

  const nodeRadius = size === "hero" ? 28 : size === "divider" ? 14 : 10;
  const leftCx = size === "hero" ? 140 : size === "divider" ? 80 : 40;
  const rightCx = size === "hero" ? 340 : size === "divider" ? 240 : 120;
  const cy = size === "hero" ? 100 : 30;

  const pathD =
    size === "hero"
      ? `M ${leftCx} ${cy} C ${leftCx + 80} ${cy - 50}, ${rightCx - 80} ${cy + 50}, ${rightCx} ${cy}`
      : size === "divider"
        ? `M ${leftCx} ${cy} C ${leftCx + 50} ${cy - 18}, ${rightCx - 50} ${cy + 18}, ${rightCx} ${cy}`
        : `M ${leftCx} ${cy} C ${leftCx + 30} ${cy - 12}, ${rightCx - 30} ${cy + 12}, ${rightCx} ${cy}`;

  const drawDuration = reduceMotion ? 0 : size === "hero" ? 1.6 : 1;
  const nodeDelay = reduceMotion ? 0 : size === "hero" ? 0.4 : 0.2;

  return (
    <svg
      className={cn("elo-svg", className)}
      width={dims.width}
      height={dims.height}
      viewBox={dims.viewBox}
      fill="none"
      aria-hidden="true"
    >
      {/* Left node */}
      <motion.circle
        cx={leftCx}
        cy={cy}
        r={nodeRadius}
        fill="hsl(177 57% 15% / 0.12)"
        stroke="hsl(177 57% 15%)"
        strokeWidth={size === "hero" ? 2 : 1.5}
        initial={reduceMotion ? undefined : { scale: 0, opacity: 0 }}
        animate={reduceMotion ? undefined : { scale: 1, opacity: 1 }}
        transition={{ duration: 0.5, delay: nodeDelay, ease: "easeOut" }}
      />

      {/* Left node inner dot */}
      <motion.circle
        cx={leftCx}
        cy={cy}
        r={nodeRadius * 0.3}
        fill="hsl(177 57% 15%)"
        initial={reduceMotion ? undefined : { scale: 0 }}
        animate={reduceMotion ? undefined : { scale: 1 }}
        transition={{ duration: 0.3, delay: nodeDelay + 0.3, ease: "easeOut" }}
      />

      {/* Connecting curve */}
      <motion.path
        d={pathD}
        stroke="hsl(31 67% 55%)"
        strokeWidth={size === "hero" ? 2.5 : 1.5}
        strokeLinecap="round"
        fill="none"
        initial={reduceMotion ? undefined : { pathLength: 0, opacity: 0 }}
        animate={reduceMotion ? undefined : { pathLength: 1, opacity: 1 }}
        transition={{ duration: drawDuration, delay: nodeDelay + 0.15, ease: [0.22, 1, 0.36, 1] }}
      />

      {/* Right node */}
      <motion.circle
        cx={rightCx}
        cy={cy}
        r={nodeRadius}
        fill="hsl(31 67% 55% / 0.12)"
        stroke="hsl(31 67% 55%)"
        strokeWidth={size === "hero" ? 2 : 1.5}
        initial={reduceMotion ? undefined : { scale: 0, opacity: 0 }}
        animate={reduceMotion ? undefined : { scale: 1, opacity: 1 }}
        transition={{ duration: 0.5, delay: nodeDelay + drawDuration * 0.6, ease: "easeOut" }}
      />

      {/* Right node inner dot */}
      <motion.circle
        cx={rightCx}
        cy={cy}
        r={nodeRadius * 0.3}
        fill="hsl(31 67% 55%)"
        initial={reduceMotion ? undefined : { scale: 0 }}
        animate={reduceMotion ? undefined : { scale: 1 }}
        transition={{
          duration: 0.3,
          delay: nodeDelay + drawDuration * 0.6 + 0.3,
          ease: "easeOut",
        }}
      />

      {/* Labels for hero size */}
      {size === "hero" && (
        <>
          <motion.text
            x={leftCx}
            y={cy + nodeRadius + 28}
            textAnchor="middle"
            fill="hsl(130 10% 93% / 0.7)"
            fontSize="11"
            fontFamily="var(--font-body), system-ui, sans-serif"
            fontWeight="600"
            initial={reduceMotion ? undefined : { opacity: 0 }}
            animate={reduceMotion ? undefined : { opacity: 1 }}
            transition={{ duration: 0.5, delay: nodeDelay + 0.6 }}
          >
            Terapeuta
          </motion.text>
          <motion.text
            x={rightCx}
            y={cy + nodeRadius + 28}
            textAnchor="middle"
            fill="hsl(130 10% 93% / 0.7)"
            fontSize="11"
            fontFamily="var(--font-body), system-ui, sans-serif"
            fontWeight="600"
            initial={reduceMotion ? undefined : { opacity: 0 }}
            animate={reduceMotion ? undefined : { opacity: 1 }}
            transition={{ duration: 0.5, delay: nodeDelay + drawDuration * 0.6 + 0.6 }}
          >
            Paciente
          </motion.text>
        </>
      )}
    </svg>
  );
}

/* ── Section divider using the elo motif ── */
export function EloDivider({ className }: { className?: string }) {
  const reduceMotion = useReducedMotion();

  return (
    <div className={cn("elo-divider", className)} aria-hidden="true">
      <motion.span
        className="elo-divider__line"
        initial={reduceMotion ? undefined : { scaleX: 0 }}
        whileInView={reduceMotion ? undefined : { scaleX: 1 }}
        viewport={{ once: true, amount: 0.5 }}
        transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
      />
      <span className="elo-divider__dot" />
      <motion.span
        className="elo-divider__line"
        initial={reduceMotion ? undefined : { scaleX: 0 }}
        whileInView={reduceMotion ? undefined : { scaleX: 1 }}
        viewport={{ once: true, amount: 0.5 }}
        transition={{ duration: 0.8, delay: 0.15, ease: [0.22, 1, 0.36, 1] }}
      />
    </div>
  );
}

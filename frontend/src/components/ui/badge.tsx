import React from "react";

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "success" | "danger" | "warning" | "info";
  glow?: boolean;
  className?: string;
}

export function Badge({
  variant = "default",
  glow = false,
  className = "",
  children,
  ...props
}: BadgeProps) {
  const baseStyles = "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold select-none border transition-all duration-300";

  const variants = {
    default: "bg-slate-800/40 text-slate-300 border-slate-700/50",
    success: `bg-emerald-950/30 text-emerald-400 border-emerald-800/40 ${
      glow ? "shadow-[0_0_12px_rgba(16,185,129,0.15)] bg-emerald-500/10" : ""
    }`,
    danger: `bg-rose-950/30 text-rose-400 border-rose-800/40 ${
      glow ? "shadow-[0_0_12px_rgba(239,68,68,0.15)] bg-rose-500/10" : ""
    }`,
    warning: `bg-amber-950/30 text-amber-400 border-amber-800/40 ${
      glow ? "shadow-[0_0_12px_rgba(245,158,11,0.15)] bg-amber-500/10" : ""
    }`,
    info: "bg-blue-950/30 text-blue-400 border-blue-800/40",
  };

  return (
    <span className={`${baseStyles} ${variants[variant]} ${className}`} {...props}>
      {children}
    </span>
  );
}

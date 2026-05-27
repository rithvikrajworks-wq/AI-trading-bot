import React from "react";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "outline" | "ghost" | "danger" | "success";
  size?: "sm" | "md" | "lg";
  className?: string;
}

export function Button({
  variant = "default",
  size = "md",
  className = "",
  children,
  disabled,
  ...props
}: ButtonProps) {
  const baseStyles =
    "inline-flex items-center justify-center font-medium rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-slate-700 disabled:opacity-50 disabled:pointer-events-none active:scale-[0.98]";

  const variants = {
    default: "bg-blue-600 hover:bg-blue-500 text-white shadow-md shadow-blue-900/25 border border-blue-500/20",
    outline: "border border-slate-700 hover:border-slate-600 bg-slate-900/20 hover:bg-slate-800/40 text-slate-200",
    ghost: "text-slate-400 hover:text-slate-100 hover:bg-slate-800/40",
    danger: "bg-red-600 hover:bg-red-500 text-white shadow-md shadow-red-900/25",
    success: "bg-emerald-600 hover:bg-emerald-500 text-white shadow-md shadow-emerald-900/25",
  };

  const sizes = {
    sm: "px-3 py-1.5 text-xs",
    md: "px-4 py-2 text-sm",
    lg: "px-6 py-3 text-base",
  };

  return (
    <button
      className={`${baseStyles} ${variants[variant]} ${sizes[size]} ${className}`}
      disabled={disabled}
      {...props}
    >
      {children}
    </button>
  );
}

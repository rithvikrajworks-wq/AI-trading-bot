import React from "react";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: boolean;
  className?: string;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ error = false, className = "", ...props }, ref) => {
    return (
      <input
        ref={ref}
        className={`w-full px-4 py-2 text-sm text-slate-100 bg-slate-950/60 border ${
          error ? "border-red-500/60 focus:ring-red-500/20" : "border-slate-800 focus:border-slate-700 focus:ring-slate-700/20"
        } rounded-lg placeholder-slate-500 focus:outline-none focus:ring-2 transition-all duration-200 ${className}`}
        {...props}
      />
    );
  }
);

Input.displayName = "Input";

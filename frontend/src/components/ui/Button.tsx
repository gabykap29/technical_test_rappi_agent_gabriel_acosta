import { useContext } from "react";
import { ThemeContext } from "@/features/agent/OperationsDashboard";
import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonVariant = "primary" | "secondary" | "ghost";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode;
  variant?: ButtonVariant;
};

export function Button({
  children,
  variant = "secondary",
  className = "",
  ...props
}: ButtonProps) {
  const { theme } = useContext(ThemeContext);
  const isDark = theme === "dark";

  const variantClasses: Record<ButtonVariant, string> = {
    primary: "bg-[image:var(--accent-gradient)] text-white hover:brightness-95",
    secondary: isDark 
      ? "text-theme border border-gray-600 bg-gray-800 hover:border-[var(--accent)]"
      : "text-theme border border-[#f0c9b8] bg-white hover:border-[var(--accent)]",
    ghost: isDark 
      ? "text-theme hover:bg-gray-800"
      : "text-theme hover:bg-[var(--accent-soft)]",
  };

  return (
    <button
      className={`focus-ring min-h-10 px-4 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-60 ${variantClasses[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}

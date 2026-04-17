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
    primary: "bg-[#16834f] text-white hover:bg-[#10683e]",
    secondary: isDark 
      ? "text-theme border border-gray-600 bg-gray-800 hover:border-green-500"
      : "text-theme border border-[#cbd9d1] bg-white hover:border-[#16834f]",
    ghost: isDark 
      ? "text-theme hover:bg-gray-800"
      : "text-theme hover:bg-[#e7f5ec]",
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

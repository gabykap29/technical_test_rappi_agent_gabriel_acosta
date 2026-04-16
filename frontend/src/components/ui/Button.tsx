import type { ButtonHTMLAttributes, ReactNode } from "react";

type ButtonVariant = "primary" | "secondary" | "ghost";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode;
  variant?: ButtonVariant;
};

const variants: Record<ButtonVariant, string> = {
  primary: "bg-[#16834f] text-white hover:bg-[#10683e]",
  secondary: "border border-[#cbd9d1] bg-white text-[#1d2421] hover:border-[#16834f]",
  ghost: "text-[#315246] hover:bg-[#e7f5ec]",
};

export function Button({
  children,
  variant = "secondary",
  className = "",
  ...props
}: ButtonProps) {
  return (
    <button
      className={`focus-ring min-h-10 px-4 py-2 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-60 ${variants[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}

import { useContext } from "react";
import { ThemeContext } from "@/features/agent/OperationsDashboard";
import type { InputHTMLAttributes, ReactNode, SelectHTMLAttributes } from "react";

type FieldProps = {
  label: string;
  help?: string;
  children: ReactNode;
};

export function Field({ label, help, children }: FieldProps) {
  const { theme } = useContext(ThemeContext);
  const isDark = theme === "dark";

  return (
    <label className="block">
      <span className="text-theme mb-1 block text-sm font-semibold">{label}</span>
      {children}
      <span className="text-theme-muted mt-1 block text-xs">{help}</span>
    </label>
  );
}

export function TextInput(props: InputHTMLAttributes<HTMLInputElement>) {
  const { theme } = useContext(ThemeContext);
  const isDark = theme === "dark";

  return (
    <input
      className={`text-theme focus-ring h-10 w-full rounded-lg border px-3 text-sm ${isDark ? 'border-gray-600 bg-gray-800' : 'border-[#cbd9d1] bg-white'}`}
      {...props}
    />
  );
}

export function SelectInput(props: SelectHTMLAttributes<HTMLSelectElement>) {
  const { theme } = useContext(ThemeContext);
  const isDark = theme === "dark";

  return (
    <select
      className={`text-theme focus-ring h-10 w-full rounded-lg border px-3 text-sm ${isDark ? 'border-gray-600 bg-gray-800' : 'border-[#cbd9d1] bg-white'}`}
      {...props}
    />
  );
}

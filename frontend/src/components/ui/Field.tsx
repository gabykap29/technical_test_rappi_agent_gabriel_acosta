import type { InputHTMLAttributes, ReactNode, SelectHTMLAttributes } from "react";

type FieldProps = {
  label: string;
  help?: string;
  children: ReactNode;
};

export function Field({ label, help, children }: FieldProps) {
  return (
    <label className="block">
      <span className="mb-1 block text-sm font-semibold text-[#29342f]">{label}</span>
      {children}
      {help ? <span className="mt-1 block text-xs text-[#66746d]">{help}</span> : null}
    </label>
  );
}

export function TextInput(props: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className="focus-ring h-10 w-full rounded-lg border border-[#cbd9d1] bg-white px-3 text-sm text-[#1d2421]"
      {...props}
    />
  );
}

export function SelectInput(props: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      className="focus-ring h-10 w-full rounded-lg border border-[#cbd9d1] bg-white px-3 text-sm text-[#1d2421]"
      {...props}
    />
  );
}

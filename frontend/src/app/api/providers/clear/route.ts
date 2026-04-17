import { NextResponse } from "next/server";
import { requestPythonApi } from "@/lib/http";

export async function POST() {
  try {
    const result = await requestPythonApi<{ status: string; cleared: number }>(
      "/providers/clear",
      { method: "POST" },
    );
    return NextResponse.json(result);
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Unknown error" },
      { status: 400 },
    );
  }
}

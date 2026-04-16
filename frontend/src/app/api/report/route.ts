import { NextResponse } from "next/server";
import { requestPythonApi } from "@/lib/http";
import type { ReportResponse } from "@/types/api";

export async function POST() {
  try {
    const report = await requestPythonApi<ReportResponse>("/report", {
      method: "POST",
      body: {},
    });
    return NextResponse.json(report);
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Unknown error" },
      { status: 400 },
    );
  }
}

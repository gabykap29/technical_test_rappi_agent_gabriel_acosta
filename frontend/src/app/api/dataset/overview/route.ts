import { NextResponse } from "next/server";
import { requestPythonApi } from "@/lib/http";
import type { DatasetOverview } from "@/types/api";

export async function GET() {
  try {
    const overview = await requestPythonApi<DatasetOverview>("/dataset/overview");
    return NextResponse.json(overview);
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Unknown error" },
      { status: 502 },
    );
  }
}

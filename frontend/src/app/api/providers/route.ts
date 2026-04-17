import { NextResponse } from "next/server";
import { requestPythonApi } from "@/lib/http";
import type { ProviderConfigPayload, ProvidersResponse } from "@/types/api";

export async function GET() {
  try {
    const providers = await requestPythonApi<ProvidersResponse>("/providers");
    return NextResponse.json(providers);
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Unknown error" },
      { status: 502 },
    );
  }
}

export async function POST(request: Request) {
  try {
    const body = (await request.json()) as ProviderConfigPayload;
    const result = await requestPythonApi<{ status: string }>("/providers", {
      method: "POST",
      body,
    });
    return NextResponse.json(result);
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Unknown error" },
      { status: 400 },
    );
  }
}

export async function DELETE() {
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

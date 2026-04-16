import { NextResponse } from "next/server";
import { requestPythonApi } from "@/lib/http";
import type { ChatRequest, ChatResponse } from "@/types/api";

export async function POST(request: Request) {
  try {
    const body = (await request.json()) as ChatRequest;
    const response = await requestPythonApi<ChatResponse>("/chat", {
      method: "POST",
      body,
    });
    return NextResponse.json(response);
  } catch (error) {
    return NextResponse.json(
      { error: error instanceof Error ? error.message : "Unknown error" },
      { status: 400 },
    );
  }
}

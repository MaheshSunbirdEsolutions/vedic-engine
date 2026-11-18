import type { NextRequest } from "next/server";
import { proxyToEngine } from "@/lib/engine-proxy";

export const dynamic = "force-dynamic";

type RouteContext = { params: Promise<{ path: string[] }> };

async function handler(req: NextRequest, { params }: RouteContext): Promise<Response> {
  const { path } = await params;
  return proxyToEngine(req, ["books", ...path]);
}

export const GET = handler;
export const HEAD = handler;

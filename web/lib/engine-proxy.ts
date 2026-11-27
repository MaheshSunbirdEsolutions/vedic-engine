import { auth } from "@clerk/nextjs/server";
import { NextRequest, NextResponse } from "next/server";

const HOP_BY_HOP_REQUEST_HEADERS = new Set([
  "host",
  "connection",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailer",
  "transfer-encoding",
  "upgrade",
  "content-length",
  "accept-encoding",
]);

const HOP_BY_HOP_RESPONSE_HEADERS = new Set([
  "connection",
  "keep-alive",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailer",
  "transfer-encoding",
  "upgrade",
  "content-encoding",
  "content-length",
]);

const NULL_BODY_STATUSES = new Set([101, 204, 205, 304]);

function engineBaseUrl(): string | null {
  const raw = process.env.ENGINE_URL?.trim();
  if (!raw) {
    if (process.env.VERCEL) return null;
    return "http://127.0.0.1:8000/";
  }
  return raw.endsWith("/") ? raw : `${raw}/`;
}

export async function proxyToEngine(req: NextRequest, segments: string[]): Promise<Response> {
  const base = engineBaseUrl();
  if (!base) {
    return NextResponse.json(
      { detail: "ENGINE_URL is not configured on Vercel. Ensure Root Directory is '.' so vercel.json service bindings inject ENGINE_URL." },
      { status: 502 },
    );
  }
  const relativePath = segments.map(encodeURIComponent).join("/");
  const target = new URL(`${relativePath}${req.nextUrl.search}`, base);
  const basePath = new URL(base).pathname.replace(/\/+$/, "");
  if (target.origin === req.nextUrl.origin && (basePath === "" || basePath === "/engine")) {
    return NextResponse.json(
      { detail: "ENGINE_URL points to the web app itself instead of the Python Vedic Engine. Remove any manual ENGINE_URL env var in Vercel so the vercel.json service binding is used." },
      { status: 502 },
    );
  }

  const headers = new Headers();
  req.headers.forEach((value, key) => {
    if (!HOP_BY_HOP_REQUEST_HEADERS.has(key.toLowerCase())) {
      headers.set(key, value);
    }
  });

  if (!headers.has("authorization")) {
    try {
      const { getToken } = await auth();
      const token = await getToken();
      if (token) {
        headers.set("authorization", `Bearer ${token}`);
      }
    } catch {
      // Unauthenticated or public calls proceed without a Bearer token.
    }
  }

  const hasBody = req.method !== "GET" && req.method !== "HEAD";
  const body = hasBody ? await req.arrayBuffer() : undefined;

  let upstream: Response;
  try {
    upstream = await fetch(target, {
      method: req.method,
      headers,
      body: body && body.byteLength > 0 ? body : undefined,
      cache: "no-store",
    });
  } catch {
    return NextResponse.json({ detail: "Cannot reach the Vedic Engine" }, { status: 502 });
  }

  const responseHeaders = new Headers();
  upstream.headers.forEach((value, key) => {
    if (!HOP_BY_HOP_RESPONSE_HEADERS.has(key.toLowerCase())) {
      responseHeaders.append(key, value);
    }
  });

  return new Response(NULL_BODY_STATUSES.has(upstream.status) ? null : upstream.body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers: responseHeaders,
  });
}

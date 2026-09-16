import { NextResponse } from 'next/server';
import { corsHeaders, isAllowedOrigin } from './lib/Mrliou_MRL_public_cors_v1.mjs';

export function middleware(request) {
  const origin = request.headers.get('origin');
  const allowed = isAllowedOrigin(origin, process.env.MRL_PUBLIC_PAGES_ORIGINS);
  if (request.method === 'OPTIONS') {
    if (!allowed) return new NextResponse(null, {status: 403});
    return new NextResponse(null, {status: 204, headers: corsHeaders(origin)});
  }
  const response = NextResponse.next();
  if (allowed) Object.entries(corsHeaders(origin)).forEach(([name, value]) => response.headers.set(name, value));
  return response;
}

export const config = {matcher: '/api/mrl/:path*'};

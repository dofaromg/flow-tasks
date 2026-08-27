import { NextResponse } from 'next/server';

// Liveness/readiness endpoint. deployment.yaml probes GET / but this gives a
// structured status for the control plane. origin_signature: MrLiouWord
export const dynamic = 'force-dynamic';

export function GET() {
  return NextResponse.json({
    ok: true,
    service: 'nextjs-frontend',
    version: '2.0.0',
    status: 'healthy',
    origin_signature: 'MrLiouWord',
    time: Date.now(),
  });
}

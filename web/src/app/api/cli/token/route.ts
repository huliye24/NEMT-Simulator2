import { getCliToken, rotateCliToken } from "@/lib/studio/cliToken";

export const dynamic = "force-dynamic";

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "content-type, x-nemt-cli-token",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
};

export async function OPTIONS() {
  return new Response(null, { status: 204, headers: CORS });
}

export async function GET() {
  const token = await getCliToken();
  return Response.json({ ok: true, token }, { headers: CORS });
}

export async function POST() {
  const token = await rotateCliToken();
  return Response.json({ ok: true, token }, { headers: CORS });
}

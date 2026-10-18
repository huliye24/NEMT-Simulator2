import type { Metadata } from "next";
import StudioApp from "@/components/trade/studio/StudioApp";

export const metadata: Metadata = {
  title: "NEMT Studio",
  description:
    "NEMT Studio — professional digital asset trading workbench with real-time market data, server-side risk controls, and DEMO execution.",
};

export default async function TradePage({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const params = await searchParams;
  return <StudioApp initialLogin={params.login === "1"} />;
}

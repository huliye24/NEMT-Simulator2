import type { Metadata } from "next";
import StudioApp from "@/components/trade/studio/StudioApp";

export const metadata: Metadata = {
  title: "NEMT Studio",
  description:
    "NEMT Studio — research-driven, strategy-first quantitative investment workspace: research, experiments, strategies, execution, risk and portfolio.",
};

export default async function TradePage({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const params = await searchParams;
  return <StudioApp initialLogin={params.login === "1"} />;
}

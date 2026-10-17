import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    id: "/trade",
    name: "NEMT Trade — 现货交易终端",
    short_name: "NEMT",
    description:
      "NEMT App V0.1 · 手机优先的 Binance Spot DEMO/Testnet 交易终端。默认不含实盘写入能力。",
    start_url: "/trade",
    scope: "/",
    display: "standalone",
    orientation: "portrait",
    background_color: "#04070c",
    theme_color: "#04070c",
    lang: "zh-CN",
    categories: ["finance", "business"],
    icons: [
      {
        src: "/icons/icon-192.png",
        sizes: "192x192",
        type: "image/png",
        purpose: "any",
      },
      {
        src: "/icons/icon-512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "any",
      },
      {
        src: "/icons/icon-maskable-512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "maskable",
      },
    ],
    shortcuts: [
      {
        name: "交易工作台",
        short_name: "交易",
        url: "/trade",
        icons: [{ src: "/icons/icon-192.png", sizes: "192x192" }],
      },
    ],
  };
}

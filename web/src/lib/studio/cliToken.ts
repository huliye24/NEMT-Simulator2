import { randomBytes } from "node:crypto";
import { mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";

const DIR = path.join(process.cwd(), ".nemt");
const FILE = path.join(DIR, "cli-token.json");

export interface CliTokenRecord {
  token: string;
  createdAt: string;
}

/** 读取 CLI token；不存在时自动生成一个并落盘到 .nemt/cli-token.json */
export async function getCliToken(): Promise<string> {
  if (process.env.NEMT_CLI_TOKEN) return process.env.NEMT_CLI_TOKEN;
  try {
    const raw = await readFile(FILE, "utf8");
    const parsed = JSON.parse(raw) as Partial<CliTokenRecord>;
    if (parsed.token) return parsed.token;
  } catch {
    /* 首次运行：没有文件就走生成逻辑 */
  }
  return rotateCliToken();
}

/** 重新生成 token（旧 token 立即失效） */
export async function rotateCliToken(): Promise<string> {
  const token = `nemt_cli_${randomBytes(12).toString("hex")}`;
  if (!process.env.NEMT_CLI_TOKEN) {
    await mkdir(DIR, { recursive: true });
    const record: CliTokenRecord = { token, createdAt: new Date().toISOString() };
    await writeFile(FILE, JSON.stringify(record, null, 2), "utf8");
  }
  return token;
}

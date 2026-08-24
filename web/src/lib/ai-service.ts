// AI Reasoning Service
// ------------------------------------------------------------------
// Today: Mock implementation with local JSON
// Tomorrow: Connect to LLM API (OpenAI, Anthropic, or self-hosted)
// ------------------------------------------------------------------

import type {
  HumanThesis,
  MarketContext,
  AIReasoning,
  FinalDecision,
  Analysis,
} from "@/lib/types";

// LLM Provider Interface (future)
interface LLMProvider {
  generateReasoning(
    thesis: HumanThesis,
    context: MarketContext
  ): Promise<AIReasoning>;
}

// Mock LLM Provider (current)
class MockLLMProvider implements LLMProvider {
  async generateReasoning(
    thesis: HumanThesis,
    context: MarketContext
  ): Promise<AIReasoning> {
    // Simulate processing delay
    await new Promise((r) => setTimeout(r, 1000));

    // Generate reasoning based on market context
    const reasoning: AIReasoning = {
      marketInterpretation: this.generateInterpretation(context),
      riskAssessment: this.assessRisk(context, thesis),
      recommendation: this.generateRecommendation(context),
      confidence: this.calculateConfidence(context),
      reasoning: this.generateReasoningSteps(context),
    };

    return reasoning;
  }

  private generateInterpretation(context: MarketContext): string {
    const interpretations: Record<string, string> = {
      MARKUP: `${context.dominantSymbol} Phase Markup confirmed. DCI at ${context.avgDci} indicates strong momentum. On-chain data shows healthy accumulation.`,
      ACCUMULATION: `${context.dominantSymbol} in Accumulation phase. DCI ${context.avgDci} suggests building base. Watch for breakout signals.`,
      DISTRIBUTION: `${context.dominantSymbol} showing Distribution signatures. DCI declining to ${context.avgDci}. Caution warranted.`,
      MARKDOWN: `${context.dominantSymbol} in Markdown phase. DCI ${context.avgDci} reflects bearish momentum. Defensive posture recommended.`,
      RECOVERY: `${context.dominantSymbol} in Recovery phase. DCI ${context.avgDci} showing early strength. Monitor confirmation.`,
      UNKNOWN: `Market phase unclear. DCI ${context.avgDci} suggests mixed signals. Await clarity.`,
    };

    return interpretations[context.phase] || interpretations.UNKNOWN;
  }

  private assessRisk(context: MarketContext, thesis: HumanThesis): {
    level: "LOW" | "MEDIUM" | "HIGH";
    factors: string[];
  } {
    const factors: string[] = [];

    if (context.avgDci > 70) factors.push("High DCI may indicate overheating");
    if (context.avgDci < 40) factors.push("Low DCI suggests weak momentum");
    if (thesis.riskFactors) factors.push(...thesis.riskFactors.split("\n").filter(Boolean));

    const level: "LOW" | "MEDIUM" | "HIGH" =
      factors.length >= 3 ? "HIGH" : factors.length >= 1 ? "MEDIUM" : "LOW";

    return { level, factors };
  }

  private generateRecommendation(context: MarketContext): "STRONG_BUY" | "BUY" | "HOLD" | "REDUCE" | "SELL" | "WAIT" {
    const recs: Record<string, "STRONG_BUY" | "BUY" | "HOLD" | "REDUCE" | "SELL" | "WAIT"> = {
      MARKUP: "BUY",
      ACCUMULATION: "HOLD",
      DISTRIBUTION: "REDUCE",
      MARKDOWN: "SELL",
      RECOVERY: "BUY",
      UNKNOWN: "WAIT",
    };

    // Adjust based on DCI
    if (context.avgDci > 75) return "STRONG_BUY";
    if (context.avgDci < 35) return "SELL";

    return recs[context.phase] || "WAIT";
  }

  private calculateConfidence(context: MarketContext): number {
    // Base confidence on DCI and phase clarity
    let confidence = context.avgDci;

    if (context.phase === "MARKUP" || context.phase === "MARKDOWN") {
      confidence += 5; // Clearer phases get boost
    }

    return Math.min(95, Math.max(50, confidence));
  }

  private generateReasoningSteps(context: MarketContext): string[] {
    const steps: string[] = [
      `DCI ${context.avgDci.toFixed(1)} indicates ${context.avgDci > 60 ? "strong" : "moderate"} directional confidence`,
      `Phase ${context.phase} confirms ${context.phase === "MARKUP" || context.phase === "RECOVERY" ? "bullish" : "bearish"} structure`,
    ];

    if (context.avgDci > 65) {
      steps.push("Volume profile supports trend continuation");
    }

    if (context.sentiment === "BULLISH") {
      steps.push("Market sentiment aligns with technicals");
    }

    return steps;
  }
}

// Future: Real LLM Provider
// class OpenAIProvider implements LLMProvider {
//   private apiKey: string;
//   private model: string;
//
//   constructor(apiKey: string, model = "gpt-4") {
//     this.apiKey = apiKey;
//     this.model = model;
//   }
//
//   async generateReasoning(thesis: HumanThesis, context: MarketContext): Promise<AIReasoning> {
//     const prompt = this.buildPrompt(thesis, context);
//     const response = await fetch("https://api.openai.com/v1/chat/completions", {
//       method: "POST",
//       headers: {
//         "Authorization": `Bearer ${this.apiKey}`,
//         "Content-Type": "application/json",
//       },
//       body: JSON.stringify({
//         model: this.model,
//         messages: [{ role: "user", content: prompt }],
//       }),
//     });
//     // Parse and return...
//   }
// }

// Service Factory
export class AIReasoningService {
  private provider: LLMProvider;

  constructor(useRealLLM = false) {
    // Toggle between mock and real LLM
    this.provider = useRealLLM
      ? (() => { throw new Error("Real LLM not configured"); })()
      : new MockLLMProvider();
  }

  async analyze(
    thesis: HumanThesis,
    context: MarketContext
  ): Promise<{ reasoning: AIReasoning; decision: FinalDecision }> {
    const reasoning = await this.provider.generateReasoning(thesis, context);

    // Generate final decision based on reasoning
    const decision = this.generateDecision(reasoning);

    return { reasoning, decision };
  }

  private generateDecision(reasoning: AIReasoning): FinalDecision {
    const action = reasoning.recommendation;

    // Size based on confidence
    let size = "0%";
    if (reasoning.confidence > 80) size = "50%";
    else if (reasoning.confidence > 65) size = "30%";
    else if (reasoning.confidence > 50) size = "10%";

    // Entry based on recommendation
    const entry = null; // Would be calculated from market data
    const stopLoss = action === "BUY" || action === "STRONG_BUY" ? null : null;
    const takeProfit = null;

    return {
      action,
      size,
      entry,
      stopLoss,
      takeProfit,
    };
  }
}

// Export singleton
export const aiService = new AIReasoningService();

// Package main provides CLI for North Star Navigator
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"strings"

	"github.com/nemt-lab/nemt-go/pkg/northstar"
)

// colors for terminal output
const (
	colorGreen  = "\033[32m"
	colorYellow = "\033[33m"
	colorRed    = "\033[31m"
	colorBlue   = "\033[34m"
	colorReset  = "\033[0m"
)

func main() {
	ctx := context.Background()

	// Create navigator
	nav := northstar.NewNavigator(ctx)
	nav.InitializeWithDefaults()

	// Parse commands
	if len(os.Args) < 2 {
		printHelp()
		os.Exit(1)
	}

	cmd := os.Args[1]

	switch cmd {
	case "status", "s":
		showStatus(nav)
	case "northstar", "ns":
		showNorthStar(nav)
	case "constellations", "c":
		showConstellations(nav)
	case "waypoints", "w":
		showWaypoints(nav, os.Args[2:])
	case "test", "t":
		runTest(nav, os.Args[2:])
	case "add-wp":
		addWaypoint(nav, os.Args[2:])
	case "complete-wp":
		completeWaypoint(nav, os.Args[2:])
	case "report", "r":
		generateReport(nav)
	case "deviation", "d":
		checkDeviation(nav)
	case "help", "h":
		printHelp()
	default:
		fmt.Printf("Unknown command: %s\n", cmd)
		printHelp()
	}
}

func showStatus(nav *northstar.Navigator) {
	fmt.Println()
	fmt.Println(strings.Repeat("=", 60))
	fmt.Println("   NEMT 北极星导航状态")
	fmt.Println(strings.Repeat("=", 60))
	fmt.Println()

	ns := nav.GetNorthStar()
	fmt.Printf("%s⭐ 北极星%s: %s\n", colorBlue, colorReset, ns.Statement)
	fmt.Println()

	// Constellations progress
	constellations := nav.GetConstellations()
	var totalProgress float64
	for _, c := range constellations {
		status := getStatusString(c.Status)
		progressBar := getProgressBar(c.Progress)
		fmt.Printf("%s %s\n", status, c.Name)
		fmt.Printf("   %s %.1f%%\n", progressBar, c.Progress)

		// KPIs
		for _, kpi := range c.KPIs {
			fmt.Printf("     - %s: %.1f/%.1f %s\n", kpi.Name, kpi.Current, kpi.Target, kpi.Unit)
		}
		fmt.Println()
		totalProgress += c.Progress
	}

	if len(constellations) > 0 {
		fmt.Printf("整体进度: %.1f%%\n", totalProgress/float64(len(constellations)))
	}

	fmt.Println()
	fmt.Println(strings.Repeat("=", 60))
}

func showNorthStar(nav *northstar.Navigator) {
	ns := nav.GetNorthStar()
	fmt.Println()
	fmt.Println(strings.Repeat("=", 60))
	fmt.Println("   ⭐ 北极星")
	fmt.Println(strings.Repeat("=", 60))
	fmt.Println()
	fmt.Printf("%s核心宣言%s:\n", colorBlue, colorReset)
	fmt.Printf("  %s\n\n", ns.Statement)

	fmt.Printf("%s核心价值观%s:\n", colorBlue, colorReset)
	for i, v := range ns.Values {
		fmt.Printf("  %d. %s\n", i+1, v)
	}
	fmt.Println()

	fmt.Printf("%s愿景%s:\n", colorBlue, colorReset)
	fmt.Printf("  %s\n", ns.Vision)
	fmt.Println()
}

func showConstellations(nav *northstar.Navigator) {
	constellations := nav.GetConstellations()
	fmt.Println()
	fmt.Println(strings.Repeat("=", 60))
	fmt.Println("   🌟 星座列表")
	fmt.Println(strings.Repeat("=", 60))
	fmt.Println()

	for _, c := range constellations {
		status := getStatusString(c.Status)
		fmt.Printf("%s %s\n", status, c.Name)
		fmt.Printf("   %s\n", c.Description)
		fmt.Printf("   进度: %.1f%% | 目标: %s\n", c.Progress, c.TargetDate.Format("2006-01-02"))

		if len(c.DependsOn) > 0 {
			fmt.Printf("   依赖: %v\n", c.DependsOn)
		}
		fmt.Println()
	}
}

func showWaypoints(nav *northstar.Navigator, args []string) {
	var constellationID string
	if len(args) > 0 {
		constellationID = args[0]
	}

	waypoints := nav.GetWaypoints(constellationID)
	fmt.Println()
	fmt.Println(strings.Repeat("=", 60))
	fmt.Println("   📍 指向标列表")
	fmt.Println(strings.Repeat("=", 60))
	fmt.Println()

	if len(waypoints) == 0 {
		fmt.Println("  暂无指向标")
	} else {
		for _, w := range waypoints {
			status := getWaypointStatus(w.Status)
			fmt.Printf("%s %s\n", status, w.Name)
			fmt.Printf("   %s\n", w.Description)
			fmt.Printf("   Output: %s\n", w.Output)
			fmt.Printf("   Progress: %s\n", w.ProgressNote)
			fmt.Printf("   进度: %.0f%% | 优先级: %d\n", w.Progress, w.Priority)
			fmt.Println()
		}
	}
}

func runTest(nav *northstar.Navigator, args []string) {
	if len(args) < 6 {
		fmt.Println("Usage: test <decision> <S> <T> <A> <R> <O>")
		fmt.Println("  S, T, A, R, O can be: yes, no, discuss")
		fmt.Println("Example: test \"使用Redis缓存\" yes yes yes yes no")
		return
	}

	decision := args[0]
	cfg := &northstar.STARTTestConfig{
		StrategyAlignment: parseTestResult(args[1]),
		TradeOffCheck:   parseTestResult(args[2]),
		AlignmentCheck:  parseTestResult(args[3]),
		Reversibility:   parseTestResult(args[4]),
		OptInCheck:     parseTestResult(args[5]),
	}

	test := nav.RunSTARTest(decision, cfg)

	fmt.Println()
	fmt.Println(strings.Repeat("=", 60))
	fmt.Println("   🌟 STAR 测试结果")
	fmt.Println(strings.Repeat("=", 60))
	fmt.Println()
	fmt.Printf("Decision: %s\n\n", test.Decision)
	fmt.Printf("S - 战略对齐: %s\n", test.StrategyAlignment.String())
	fmt.Printf("T - 权衡检验: %s\n", test.TradeOffCheck.String())
	fmt.Printf("A - 目标对齐: %s\n", test.AlignmentCheck.String())
	fmt.Printf("R - 可逆性评估: %s\n", test.Reversibility.String())
	fmt.Printf("O - 主动选择: %s\n", test.OptInCheck.String())
	fmt.Println()
	fmt.Printf("YES 数量: %d\n", test.YesCount)
	fmt.Printf("结论: %s\n", test.Conclusion.String())
	fmt.Printf("建议: %s\n", test.Recommendation)
	fmt.Println()
}

func addWaypoint(nav *northstar.Navigator, args []string) {
	if len(args) < 3 {
		fmt.Println("Usage: add-wp <constellation_id> <name> <description>")
		return
	}

	constellationID := args[0]
	name := args[1]
	description := strings.Join(args[2:], " ")

	wp := &northstar.Waypoint{
		Name:           name,
		Description:    description,
		ConstellationID: constellationID,
		Status:         northstar.WaypointPending,
		Progress:       0,
		Priority:       3,
	}

	if err := nav.AddWaypoint(wp); err != nil {
		fmt.Printf("Error: %v\n", err)
	} else {
		fmt.Printf("Added waypoint: %s\n", name)
	}
}

func completeWaypoint(nav *northstar.Navigator, args []string) {
	if len(args) < 1 {
		fmt.Println("Usage: complete-wp <waypoint_id>")
		return
	}

	id := args[0]
	if err := nav.CompleteWaypoint(id); err != nil {
		fmt.Printf("Error: %v\n", err)
	} else {
		fmt.Printf("Completed waypoint: %s\n", id)
	}
}

func generateReport(nav *northstar.Navigator) {
	report := nav.GenerateReport()
	json, err := report.ToJSON()
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		return
	}

	fmt.Println(json)
}

func checkDeviation(nav *northstar.Navigator) {
	signals := nav.CheckDeviation()

	fmt.Println()
	fmt.Println(strings.Repeat("=", 60))
	fmt.Println("   🔔 偏离检测")
	fmt.Println(strings.Repeat("=", 60))
	fmt.Println()

	if len(signals) == 0 {
		fmt.Printf("%s✓ 无偏离信号%s\n", colorGreen, colorReset)
	} else {
		for _, s := range signals {
			level := colorYellow
			if s.Level == northstar.DeviationSevere {
				level = colorRed
			}
			fmt.Printf("%s[%s]%s %s\n", level, getDeviationLevel(s.Level), colorReset, s.Message)
			fmt.Printf("   行动: %s\n\n", s.Action)
		}
	}
	fmt.Println()
}

func printHelp() {
	fmt.Println(`
NEMT 北极星导航 CLI
==================

Commands:
  status, s          显示整体状态
  northstar, ns       显示北极星定义
  constellations, c   显示星座列表
  waypoints, w [id]  显示指向标列表
  test, t            运行 STAR 测试
  add-wp             添加指向标
  complete-wp         完成指向标
  report, r          生成进度报告 (JSON)
  deviation, d       检测偏离
  help, h            显示帮助
`)
}

// Helper functions

func getStatusString(status northstar.ConstellationStatus) string {
	switch status {
	case northstar.ConstellationPending:
		return "⏸️  待开始"
	case northstar.ConstellationInProgress:
		return "🚀 进行中"
	case northstar.ConstellationCompleted:
		return "✅ 完成"
	case northstar.ConstellationBlocked:
		return "🚫 阻塞"
	default:
		return "❓ 未知"
	}
}

func getWaypointStatus(status northstar.WaypointStatus) string {
	switch status {
	case northstar.WaypointPending:
		return "⏸️"
	case northstar.WaypointInProgress:
		return "🚀"
	case northstar.WaypointCompleted:
		return "✅"
	case northstar.WaypointCancelled:
		return "❌"
	default:
		return "❓"
	}
}

func getDeviationLevel(level northstar.DeviationLevel) string {
	switch level {
	case northstar.DeviationMinor:
		return "轻微"
	case northstar.DeviationModerate:
		return "中度"
	case northstar.DeviationSevere:
		return "严重"
	default:
		return "未知"
	}
}

func getProgressBar(progress float64) string {
	const width = 30
	filled := int(progress / 100 * float64(width))

	var sb strings.Builder
	sb.WriteString("[")
	for i := 0; i < width; i++ {
		if i < filled {
			sb.WriteString("█")
		} else {
			sb.WriteString("░")
		}
	}
	sb.WriteString("]")
	return sb.String()
}

func parseTestResult(s string) northstar.TestResult {
	switch strings.ToLower(s) {
	case "yes", "y":
		return northstar.TestYes
	case "no", "n":
		return northstar.TestNo
	case "discuss", "d":
		return northstar.TestNeedsDiscussion
	default:
		return northstar.TestNo
	}
}

// Need to import encoding/json for ToJSON
var _ = json.Marshal

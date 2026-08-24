// Package northstar provides the North Star Navigation system for NEMT
// 北极星导航系统 - 目标驱动的开发决策框架
//
// Core concepts:
// - NorthStar (L0): Ultimate direction, answers "why does this exist?"
// - Constellation (L1): Milestones, 3-12 months horizon
// - Waypoint (L2): Daily/weekly tasks
//
// Decision framework:
// - STAR Test: Strategy, Trade-off, Alignment, Reversibility, Opt-in
// - Decision Matrix: 4 quadrants based on strategic value and reversibility
package northstar

import (
	"context"
	"encoding/json"
	"fmt"
	"sync"
	"time"
)

// ============================================================================
// North Star (L0) - The Ultimate Direction
// ============================================================================

// NorthStar represents the L0 level goal - the ultimate purpose
type NorthStar struct {
	ID          string    `json:"id"`
	Statement   string    `json:"statement"`    // The core statement
	Values      []string  `json:"values"`        // Core values
	Vision      string    `json:"vision"`       // 3-5 year vision
	CreatedAt   time.Time `json:"created_at"`
	UpdatedAt   time.Time `json:"updated_at"`
}

// NewNorthStar creates a new North Star
func NewNorthStar(statement string, values []string, vision string) *NorthStar {
	now := time.Now()
	return &NorthStar{
		ID:        fmt.Sprintf("ns_%d", now.UnixNano()),
		Statement: statement,
		Values:    values,
		Vision:    vision,
		CreatedAt: now,
		UpdatedAt: now,
	}
}

// NEMT Default North Star
var DefaultNorthStar = &NorthStar{
	ID:        "nemt_northstar",
	Statement: "构建一个让策略在生态中生存、竞争、进化的金融系统",
	Values: []string{
		"策略是生物体，不是规则集",
		"系统适应市场，不预测市场",
		"风控优先级高于收益",
		"民主化算法交易",
	},
	Vision: "成为最易用的量化交易操作系统",
}

// ============================================================================
// Constellation (L1) - Milestones
// ============================================================================

// Constellation represents the L1 level goal - milestones
type Constellation struct {
	ID          string           `json:"id"`
	Name        string           `json:"name"`
	Description string           `json:"description"`
	KPIs        []*KPI          `json:"kpis"`                 // Measurable KPIs
	StartDate   time.Time       `json:"start_date"`
	TargetDate  time.Time       `json:"target_date"`          // Q1, Q2, etc.
	Status      ConstellationStatus `json:"status"`
	Progress    float64         `json:"progress"`             // 0-100%
	Waypoints   []*Waypoint     `json:"waypoints"`            // Child waypoints
	DependsOn   []string        `json:"depends_on"`           // Dependencies
	CreatedAt   time.Time       `json:"created_at"`
	UpdatedAt   time.Time       `json:"updated_at"`
}

// ConstellationStatus represents the status of a constellation
type ConstellationStatus int

const (
	ConstellationPending ConstellationStatus = iota
	ConstellationInProgress
	ConstellationCompleted
	ConstellationBlocked
)

// KPI represents a measurable key performance indicator
type KPI struct {
	ID       string  `json:"id"`
	Name     string  `json:"name"`
	Target   float64 `json:"target"`
	Current  float64 `json:"current"`
	Unit     string  `json:"unit"`
	Deadline time.Time `json:"deadline"`
}

// Progress calculates the KPI progress
func (k *KPI) Progress() float64 {
	if k.Target == 0 {
		return 0
	}
	pct := (k.Current / k.Target) * 100
	if pct > 100 {
		pct = 100
	}
	return pct
}

// ============================================================================
// Waypoint (L2) - Daily/Weekly Tasks
// ============================================================================

// Waypoint represents the L2 level goal - concrete tasks
type Waypoint struct {
	ID           string       `json:"id"`
	Name         string       `json:"name"`
	Description  string       `json:"description"`
	ConstellationID string   `json:"constellation_id"`
	ParentKPIID  string      `json:"parent_kpi_id"`
	Output       string      `json:"output"`               // Expected output
	Acceptance   string      `json:"acceptance"`           // Acceptance criteria
	ProgressNote string      `json:"progress_note"`        // Progress statement
	Status       WaypointStatus `json:"status"`
	Progress     float64     `json:"progress"`
	Priority     int         `json:"priority"`           // 1-5
	EstimatedHrs float64     `json:"estimated_hours"`
	ActualHrs    float64     `json:"actual_hours"`
	Tags         []string    `json:"tags"`
	CreatedAt    time.Time   `json:"created_at"`
	UpdatedAt    time.Time   `json:"updated_at"`
	CompletedAt  *time.Time  `json:"completed_at,omitempty"`
}

// WaypointStatus represents the status of a waypoint
type WaypointStatus int

const (
	WaypointPending WaypointStatus = iota
	WaypointInProgress
	WaypointCompleted
	WaypointCancelled
)

// ============================================================================
// STAR Test - Decision Framework
// ============================================================================

// STARTTest represents the 5-question decision test
type STARTTest struct {
	Decision      string    `json:"decision"`
	Timestamp     time.Time `json:"timestamp"`

	// Questions
	StrategyAlignment   TestResult `json:"strategy_alignment"`    // S
	TradeOffCheck       TestResult `json:"trade_off_check"`       // T
	AlignmentCheck      TestResult `json:"alignment_check"`       // A
	Reversibility       TestResult `json:"reversibility"`         // R
	OptInCheck          TestResult `json:"opt_in_check"`          // O

	// Analysis
	Sacrifice      string `json:"sacrifice"`       // What is sacrificed
	Gain           string `json:"gain"`            // What is gained
	Constellation  string `json:"constellation"`   // Which constellation
	ReversibilityLevel ReversibilityLevel `json:"reversibility_level"`
	IsActiveChoice bool   `json:"is_active_choice"` // Proactive vs reactive

	// Conclusion
	YesCount       int              `json:"yes_count"`
	Conclusion     TestConclusion   `json:"conclusion"`
	Recommendation string          `json:"recommendation"`
}

// TestResult represents the result of a test question
type TestResult int

const (
	TestNo TestResult = iota
	TestYes
	TestNeedsDiscussion
)

func (r TestResult) String() string {
	switch r {
	case TestYes:
		return "YES"
	case TestNo:
		return "NO"
	case TestNeedsDiscussion:
		return "需要讨论"
	default:
		return "未知"
	}
}

// TestConclusion represents the conclusion of a STAR test
type TestConclusion int

const (
	ConclusionAbandon TestConclusion = iota
	ConclusionConsider
	ConclusionDiscuss
	ConclusionRecommended
	ConclusionStronglyRecommended
)

func (c TestConclusion) String() string {
	switch c {
	case ConclusionAbandon:
		return "建议放弃"
	case ConclusionConsider:
		return "谨慎考虑"
	case ConclusionDiscuss:
		return "需要讨论"
	case ConclusionRecommended:
		return "建议执行"
	case ConclusionStronglyRecommended:
		return "强烈建议执行"
	default:
		return "未知"
	}
}

// ReversibilityLevel represents how reversible a decision is
type ReversibilityLevel int

const (
	ReversibilityLow ReversibilityLevel = iota // > 1 week rollback
	ReversibilityMedium                        // 1 day to 1 week
	ReversibilityHigh                         // < 1 hour rollback
)

// NewSTARTTest creates a new STAR test
func NewSTARTest(decision string) *STARTTest {
	return &STARTTest{
		Decision:  decision,
		Timestamp: time.Now(),
	}
}

// Run executes the STAR test and returns conclusion
func (t *STARTTest) Run() *STARTTest {
	t.YesCount = 0

	// Count YESs
	if t.StrategyAlignment == TestYes {
		t.YesCount++
	}
	if t.TradeOffCheck == TestYes {
		t.YesCount++
	}
	if t.AlignmentCheck == TestYes {
		t.YesCount++
	}
	if t.Reversibility == TestYes {
		t.YesCount++
	}
	if t.OptInCheck == TestYes {
		t.YesCount++
	}

	// Determine conclusion
	switch t.YesCount {
	case 5:
		t.Conclusion = ConclusionStronglyRecommended
		t.Recommendation = "立即执行"
	case 4:
		t.Conclusion = ConclusionRecommended
		t.Recommendation = "可以执行，监控风险"
	case 3:
		t.Conclusion = ConclusionDiscuss
		t.Recommendation = "需要进一步论证"
	default:
		t.Conclusion = ConclusionAbandon
		t.Recommendation = "建议放弃或重新设计"
	}

	return t
}

// String returns a human-readable summary
func (t *STARTTest) String() string {
	conclusionStr := "Unknown"
	switch t.Conclusion {
	case ConclusionAbandon:
		conclusionStr = "建议放弃"
	case ConclusionConsider:
		conclusionStr = "谨慎考虑"
	case ConclusionDiscuss:
		conclusionStr = "需要讨论"
	case ConclusionRecommended:
		conclusionStr = "建议执行"
	case ConclusionStronglyRecommended:
		conclusionStr = "强烈建议执行"
	}

	return fmt.Sprintf(`STAR Test: %s
  S - 战略对齐: %s
  T - 权衡检验: %s
  A - 目标对齐: %s
  R - 可逆性评估: %s
  O - 主动选择: %s
  YES数量: %d
  结论: %s (%s)`, t.Decision,
		testResultString(t.StrategyAlignment),
		testResultString(t.TradeOffCheck),
		testResultString(t.AlignmentCheck),
		testResultString(t.Reversibility),
		testResultString(t.OptInCheck),
		t.YesCount,
		conclusionStr,
		t.Recommendation,
	)
}

func testResultString(r TestResult) string {
	switch r {
	case TestYes:
		return "YES"
	case TestNo:
		return "NO"
	case TestNeedsDiscussion:
		return "需要讨论"
	default:
		return "未知"
	}
}

// ============================================================================
// Decision Matrix - 4 Quadrants
// ============================================================================

// DecisionQuadrant represents the quadrant in decision matrix
type DecisionQuadrant int

const (
	QuadrantHighRisk DecisionQuadrant = iota // Low strategic, Low reversible
	QuadrantExplore                          // Low strategic, High reversible
	QuadrantStrategic                        // High strategic, Low reversible
	QuadrantPriority                         // High strategic, High reversible
)

// DecisionMatrix classifies a decision based on strategic value and reversibility
type DecisionMatrix struct {
	StrategicValue  float64           `json:"strategic_value"`   // 0-100
	Reversibility   ReversibilityLevel `json:"reversibility"`
	Quadrant        DecisionQuadrant  `json:"quadrant"`
	Action          string            `json:"action"`
	Strategy        []string          `json:"strategy"`
}

// Classify determines the quadrant based on strategic value and reversibility
func (m *DecisionMatrix) Classify() *DecisionMatrix {
	m.StrategicValue = m.StrategicValue / 100 // Normalize to 0-1

	if m.StrategicValue >= 0.5 {
		if m.Reversibility >= ReversibilityMedium {
			m.Quadrant = QuadrantPriority
			m.Action = "立即执行"
			m.Strategy = []string{
				"列入计划",
				"分配资源",
				"设置验收标准",
				"执行",
				"验证效果",
			}
		} else {
			m.Quadrant = QuadrantStrategic
			m.Action = "规划后执行"
			m.Strategy = []string{
				"深入论证",
				"寻找替代方案",
				"制定详细计划",
				"设计回滚方案",
				"分阶段推进",
				"持续监控",
			}
		}
	} else {
		if m.Reversibility >= ReversibilityMedium {
			m.Quadrant = QuadrantExplore
			m.Action = "小成本试错"
			m.Strategy = []string{
				"定义实验目标",
				"设置实验期限",
				"定义成功/失败标准",
				"执行",
				"评估结果",
				"决定：扩大/放弃",
			}
		} else {
			m.Quadrant = QuadrantHighRisk
			m.Action = "谨慎或放弃"
			m.Strategy = []string{
				"重新评估：为什么非做不可",
				"寻找替代方案",
				"考虑是否可以提高可逆性",
				"如果没有好方案 → 放弃",
			}
		}
	}

	return m
}

// ============================================================================
// Deviation Detection - 偏离矫正机制
// ============================================================================

// DeviationLevel represents the severity of deviation
type DeviationLevel int

const (
	DeviationMinor DeviationLevel = iota // < 1 day, observe
	DeviationModerate                   // 1-3 days, re-evaluate
	DeviationSevere                     // > 1 week, major adjustment
)

// DeviationSignal represents a warning signal
type DeviationSignal struct {
	ID        string         `json:"id"`
	Level     DeviationLevel `json:"level"`
	Type      string         `json:"type"`
	Message   string         `json:"message"`
	Timestamp time.Time      `json:"timestamp"`
	Evidence  string         `json:"evidence"`
	Action    string         `json:"action"`
}

// Deviation represents a detected deviation from the North Star
type Deviation struct {
	ID           string         `json:"id"`
	Type         string         `json:"type"`
	Level        DeviationLevel `json:"level"`
	Description  string         `json:"description"`
	Cause        string         `json:"cause"`
	DetectedAt   time.Time      `json:"detected_at"`
	Duration     time.Duration   `json:"duration"`
	AffectedArea string         `json:"affected_area"` // Constellation or Waypoint
	Correction   *Correction     `json:"correction,omitempty"`
}

// Correction represents the correction plan
type Correction struct {
	Plan          string    `json:"plan"`
	Steps         []string  `json:"steps"`
	Status        string    `json:"status"`
	StartedAt     time.Time `json:"started_at"`
	CompletedAt   *time.Time `json:"completed_at,omitempty"`
	Verified      bool      `json:"verified"`
}

// ============================================================================
// North Star Navigator - Core Engine
// ============================================================================

// Navigator is the main North Star navigation engine
type Navigator struct {
	northStar   *NorthStar
	constellations []*Constellation
	waypoints   []*Waypoint
	tests       []*STARTTest
	deviations  []*Deviation

	mu sync.RWMutex
	ctx context.Context
}

// NewNavigator creates a new North Star Navigator
func NewNavigator(ctx context.Context) *Navigator {
	return &Navigator{
		northStar:    DefaultNorthStar,
		constellations: make([]*Constellation, 0),
		waypoints:    make([]*Waypoint, 0),
		tests:        make([]*STARTTest, 0),
		deviations:   make([]*Deviation, 0),
		ctx:          ctx,
	}
}

// SetNorthStar sets the North Star
func (n *Navigator) SetNorthStar(ns *NorthStar) {
	n.mu.Lock()
	defer n.mu.Unlock()
	n.northStar = ns
}

// GetNorthStar returns the current North Star
func (n *Navigator) GetNorthStar() *NorthStar {
	n.mu.RLock()
	defer n.mu.RUnlock()
	return n.northStar
}

// ============================================================================
// Constellation Management
// ============================================================================

// AddConstellation adds a new constellation
func (n *Navigator) AddConstellation(c *Constellation) error {
	n.mu.Lock()
	defer n.mu.Unlock()

	c.ID = fmt.Sprintf("constellation_%d", time.Now().UnixNano())
	c.CreatedAt = time.Now()
	c.UpdatedAt = time.Now()

	// Check dependencies
	for _, dep := range c.DependsOn {
		found := false
		for _, existing := range n.constellations {
			if existing.ID == dep || existing.Name == dep {
				found = true
				break
			}
		}
		if !found {
			return fmt.Errorf("dependency not found: %s", dep)
		}
	}

	n.constellations = append(n.constellations, c)
	return nil
}

// GetConstellation returns a constellation by ID
func (n *Navigator) GetConstellation(id string) *Constellation {
	n.mu.RLock()
	defer n.mu.RUnlock()

	for _, c := range n.constellations {
		if c.ID == id || c.Name == id {
			return c
		}
	}
	return nil
}

// GetConstellations returns all constellations
func (n *Navigator) GetConstellations() []*Constellation {
	n.mu.RLock()
	defer n.mu.RUnlock()
	return n.constellations
}

// UpdateConstellationProgress updates progress based on waypoints
func (n *Navigator) UpdateConstellationProgress(id string) {
	n.mu.Lock()
	defer n.mu.Unlock()

	for _, c := range n.constellations {
		if c.ID == id || c.Name == id {
			if len(c.Waypoints) == 0 {
				c.Progress = 0
				continue
			}

			var completed float64
			for _, w := range c.Waypoints {
				if w.Status == WaypointCompleted {
					completed++
				}
			}
			c.Progress = (completed / float64(len(c.Waypoints))) * 100
			c.UpdatedAt = time.Now()
			break
		}
	}
}

// ============================================================================
// Waypoint Management
// ============================================================================

// AddWaypoint adds a new waypoint to a constellation
func (n *Navigator) AddWaypoint(w *Waypoint) error {
	n.mu.Lock()
	defer n.mu.Unlock()

	// Verify constellation exists
	found := false
	for _, c := range n.constellations {
		if c.ID == w.ConstellationID || c.Name == w.ConstellationID {
			found = true
			break
		}
	}
	if !found {
		return fmt.Errorf("constellation not found: %s", w.ConstellationID)
	}

	w.ID = fmt.Sprintf("waypoint_%d", time.Now().UnixNano())
	w.CreatedAt = time.Now()
	w.UpdatedAt = time.Now()

	n.waypoints = append(n.waypoints, w)
	return nil
}

// GetWaypoints returns waypoints, optionally filtered by constellation
func (n *Navigator) GetWaypoints(constellationID string) []*Waypoint {
	n.mu.RLock()
	defer n.mu.RUnlock()

	result := make([]*Waypoint, 0)
	for _, w := range n.waypoints {
		if constellationID == "" || w.ConstellationID == constellationID {
			result = append(result, w)
		}
	}
	return result
}

// CompleteWaypoint marks a waypoint as completed
func (n *Navigator) CompleteWaypoint(id string) error {
	n.mu.Lock()
	defer n.mu.Unlock()

	for _, w := range n.waypoints {
		if w.ID == id {
			now := time.Now()
			w.Status = WaypointCompleted
			w.Progress = 100
			w.CompletedAt = &now
			w.UpdatedAt = now

			// Update constellation progress
			n.updateConstellationProgressLocked(w.ConstellationID)
			return nil
		}
	}
	return fmt.Errorf("waypoint not found: %s", id)
}

// updateConstellationProgressLocked updates constellation progress (must hold lock)
func (n *Navigator) updateConstellationProgressLocked(constellationID string) {
	for _, c := range n.constellations {
		if c.ID == constellationID {
			waypoints := n.getWaypointsForConstellationLocked(constellationID)
			if len(waypoints) == 0 {
				c.Progress = 0
				continue
			}

			var completed float64
			for _, w := range waypoints {
				if w.Status == WaypointCompleted {
					completed++
				}
			}
			c.Progress = (completed / float64(len(waypoints))) * 100
			c.UpdatedAt = time.Now()
			break
		}
	}
}

// getWaypointsForConstellationLocked returns waypoints for a constellation (must hold lock)
func (n *Navigator) getWaypointsForConstellationLocked(constellationID string) []*Waypoint {
	result := make([]*Waypoint, 0)
	for _, w := range n.waypoints {
		if w.ConstellationID == constellationID {
			result = append(result, w)
		}
	}
	return result
}

// ============================================================================
// STAR Test Management
// ============================================================================

// RunSTARTTest runs a STAR test for a decision
func (n *Navigator) RunSTARTest(decision string, cfg *STARTTestConfig) *STARTTest {
	test := NewSTARTest(decision)

	if cfg != nil {
		test.StrategyAlignment = cfg.StrategyAlignment
		test.TradeOffCheck = cfg.TradeOffCheck
		test.AlignmentCheck = cfg.AlignmentCheck
		test.Reversibility = cfg.Reversibility
		test.OptInCheck = cfg.OptInCheck
		test.Sacrifice = cfg.Sacrifice
		test.Gain = cfg.Gain
		test.Constellation = cfg.Constellation
		test.IsActiveChoice = cfg.IsActiveChoice
	}

	test.Run()

	n.mu.Lock()
	defer n.mu.Unlock()
	n.tests = append(n.tests, test)

	return test
}

// STARTTestConfig is the configuration for running a STAR test
type STARTTestConfig struct {
	StrategyAlignment TestResult
	TradeOffCheck    TestResult
	AlignmentCheck   TestResult
	Reversibility    TestResult
	OptInCheck       TestResult
	Sacrifice        string
	Gain             string
	Constellation    string
	IsActiveChoice   bool
}

// GetTests returns all STAR tests
func (n *Navigator) GetTests() []*STARTTest {
	n.mu.RLock()
	defer n.mu.RUnlock()
	return n.tests
}

// ============================================================================
// Deviation Detection
// ============================================================================

// CheckDeviation checks for deviations and returns detected ones
func (n *Navigator) CheckDeviation() []*DeviationSignal {
	n.mu.RLock()
	defer n.mu.RUnlock()

	signals := make([]*DeviationSignal, 0)
	now := time.Now()

	// Check 1: Waypoints without constellation alignment
	for _, w := range n.waypoints {
		if w.Status == WaypointInProgress {
			// Check if waypoint is stuck (no progress in 3 days)
			if now.Sub(w.UpdatedAt) > 72*time.Hour {
				signals = append(signals, &DeviationSignal{
					ID:        fmt.Sprintf("signal_%d", now.UnixNano()),
					Level:     DeviationMinor,
					Type:      "stagnation",
					Message:   fmt.Sprintf("Waypoint '%s' has no progress in 3+ days", w.Name),
					Timestamp: now,
					Action:    "Review and either complete or cancel",
				})
			}
		}
	}

	// Check 2: Constellation with overdue KPIs
	for _, c := range n.constellations {
		if c.Status == ConstellationInProgress {
			for _, kpi := range c.KPIs {
				if now.After(kpi.Deadline) && kpi.Current < kpi.Target {
					signals = append(signals, &DeviationSignal{
						ID:        fmt.Sprintf("signal_%d", now.UnixNano()),
						Level:     DeviationModerate,
						Type:      "overdue_kpi",
						Message:   fmt.Sprintf("KPI '%s' is overdue", kpi.Name),
						Timestamp: now,
						Action:    "Re-evaluate timeline or adjust scope",
					})
				}
			}
		}
	}

	// Check 3: Too many pending waypoints
	pendingCount := 0
	for _, w := range n.waypoints {
		if w.Status == WaypointPending {
			pendingCount++
		}
	}
	if pendingCount > 20 {
		signals = append(signals, &DeviationSignal{
			ID:        fmt.Sprintf("signal_%d", now.UnixNano()),
			Level:     DeviationMinor,
			Type:      "backlog",
			Message:   fmt.Sprintf("Too many pending waypoints: %d", pendingCount),
			Timestamp: now,
			Action:    "Prioritize and prune backlog",
		})
	}

	return signals
}

// ============================================================================
// Progress Reporting
// ============================================================================

// ProgressReport generates a comprehensive progress report
type ProgressReport struct {
	NorthStar        *NorthStar      `json:"north_star"`
	OverallProgress  float64         `json:"overall_progress"`
	Constellations   []*Constellation `json:"constellations"`
	RecentTests      []*STARTTest    `json:"recent_tests"`
	ActiveDeviations []*Deviation    `json:"active_deviations"`
	TodayWaypoints   []*Waypoint     `json:"today_waypoints"`
	GeneratedAt      time.Time       `json:"generated_at"`
}

// GenerateReport generates a progress report
func (n *Navigator) GenerateReport() *ProgressReport {
	n.mu.RLock()
	defer n.mu.RUnlock()

	report := &ProgressReport{
		NorthStar:    n.northStar,
		GeneratedAt:  time.Now(),
	}

	// Calculate overall progress
	if len(n.constellations) > 0 {
		var total float64
		for _, c := range n.constellations {
			total += c.Progress
		}
		report.OverallProgress = total / float64(len(n.constellations))
	}

	report.Constellations = n.constellations

	// Recent tests (last 10)
	if len(n.tests) > 10 {
		report.RecentTests = n.tests[len(n.tests)-10:]
	} else {
		report.RecentTests = n.tests
	}

	report.ActiveDeviations = n.deviations

	// Today's waypoints
	today := time.Now().Truncate(24 * time.Hour)
	for _, w := range n.waypoints {
		if w.CreatedAt.After(today) || (w.CompletedAt != nil && w.CompletedAt.After(today)) {
			report.TodayWaypoints = append(report.TodayWaypoints, w)
		}
	}

	return report
}

// ToJSON returns the report as JSON
func (r *ProgressReport) ToJSON() (string, error) {
	data, err := json.MarshalIndent(r, "", "  ")
	if err != nil {
		return "", err
	}
	return string(data), nil
}

// ============================================================================
// NEMT Default Constellations
// ============================================================================

// DefaultConstellations returns the default NEMT constellations
func DefaultConstellations() []*Constellation {
	now := time.Now()
	q1 := now.AddDate(0, 3, 0)
	q2 := now.AddDate(0, 6, 0)
	q3 := now.AddDate(0, 9, 0)
	q4 := now.AddDate(0, 12, 0)

	return []*Constellation{
		{
			ID:          "constellation_a",
			Name:        "A: 可运行的多策略回测引擎",
			Description: "构建支持多种策略的回测系统",
			KPIs: []*KPI{
				{ID: "kpi_a1", Name: "策略类型支持", Target: 5, Unit: "种"},
				{ID: "kpi_a2", Name: "回测时间", Target: 60, Unit: "秒/策略"},
				{ID: "kpi_a3", Name: "回测报告完整度", Target: 100, Unit: "%"},
			},
			StartDate:  now,
			TargetDate: q1,
			Status:     ConstellationInProgress,
			Progress:   0,
		},
		{
			ID:          "constellation_b",
			Name:        "B: 策略淘汰机制生效",
			Description: "实现策略的自然选择",
			KPIs: []*KPI{
				{ID: "kpi_b1", Name: "胜率阈值", Target: 40, Unit: "%"},
				{ID: "kpi_b2", Name: "淘汰准确率", Target: 70, Unit: "%"},
			},
			StartDate:  q1,
			TargetDate: q2,
			Status:     ConstellationPending,
			Progress:   0,
			DependsOn:  []string{"constellation_a"},
		},
		{
			ID:          "constellation_c",
			Name:        "C: 大脑层动态权重分配",
			Description: "实现策略权重的动态调整",
			KPIs: []*KPI{
				{ID: "kpi_c1", Name: "夏普比率", Target: 1.5, Unit: ""},
				{ID: "kpi_c2", Name: "权重调整响应时间", Target: 5, Unit: "分钟"},
			},
			StartDate:  q2,
			TargetDate: q3,
			Status:     ConstellationPending,
			Progress:   0,
			DependsOn:  []string{"constellation_b"},
		},
		{
			ID:          "constellation_d",
			Name:        "D: 实盘接入",
			Description: "连接真实市场进行交易",
			KPIs: []*KPI{
				{ID: "kpi_d1", Name: "日交易量", Target: 100, Unit: "笔"},
				{ID: "kpi_d2", Name: "执行延迟", Target: 100, Unit: "毫秒"},
			},
			StartDate:  q3,
			TargetDate: q4,
			Status:     ConstellationPending,
			Progress:   0,
			DependsOn:  []string{"constellation_c"},
		},
	}
}

// InitializeWithDefaults initializes the navigator with NEMT defaults
func (n *Navigator) InitializeWithDefaults() {
	n.mu.Lock()
	defer n.mu.Unlock()

	n.northStar = DefaultNorthStar
	n.constellations = DefaultConstellations()
}

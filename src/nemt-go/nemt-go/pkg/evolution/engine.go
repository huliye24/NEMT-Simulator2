// Package evolution provides self-evolution capabilities for NEMT
package evolution

import (
	"context"
	"fmt"
	"sync"
	"time"

	"github.com/google/uuid"
)

// ============================================================================
// Evolution Engine
// ============================================================================

// Config holds evolution configuration
type Config struct {
	PopulationSize int
	Generations    int
	MutationRate  float64
	CrossoverRate float64
	EliteCount    int
}

// DefaultConfig returns default evolution config
func DefaultConfig() *Config {
	return &Config{
		PopulationSize: 50,
		Generations:    100,
		MutationRate:   0.1,
		CrossoverRate:  0.7,
		EliteCount:     5,
	}
}

// Engine is the main evolution engine
type Engine struct {
	cfg     *Config
	genes   *GenePool
	fitness FitnessEvaluator
	mu      sync.RWMutex
}

// GenePool manages available genes
type GenePool struct {
	genes     []*Gene
	constraint ConstraintChecker
}

type Gene struct {
	ID          string
	Name        string
	Description string
	Code        string
	Type        GeneType
	Parameters  map[string]interface{}
	Metadata    GeneMetadata
}

type GeneMetadata struct {
	Author      string
	Version     string
	CreatedAt   time.Time
	TestedCount int
	SuccessRate float64
}

type GeneType string

const (
	GeneSignal   GeneType = "signal"
	GeneRisk     GeneType = "risk"
	GeneExecution GeneType = "execution"
	GeneFilter   GeneType = "filter"
)

// NewEngine creates a new evolution engine
func NewEngine(cfg *Config) *Engine {
	return &Engine{
		cfg:     cfg,
		genes:   NewGenePool(),
		fitness: *NewFitnessEvaluator(),
	}
}

// Evolve runs the evolution process
func (e *Engine) Evolve(ctx context.Context, population []*Individual) ([]*Individual, error) {
	if len(population) == 0 {
		population = e.initializePopulation()
	}

	e.mu.Lock()
	defer e.mu.Unlock()

	for gen := 0; gen < e.cfg.Generations; gen++ {
		select {
		case <-ctx.Done():
			return nil, ctx.Err()
		default:
		}

		// Evaluate fitness
		for _, ind := range population {
			ind.Fitness = e.fitness.Evaluate(ind)
		}

		// Sort by fitness (descending)
		e.sortByFitness(population)

		// Log progress
		fmt.Printf("Generation %d: Best fitness = %.4f\n", gen, population[0].Fitness)

		// Create next generation
		population = e.createNextGeneration(population)
	}

	return population, nil
}

// initializePopulation creates initial population
func (e *Engine) initializePopulation() []*Individual {
	population := make([]*Individual, e.cfg.PopulationSize)

	for i := 0; i < e.cfg.PopulationSize; i++ {
		genes := make([]*Gene, 0)
		// Randomly select genes for each individual
		for _, g := range e.genes.genes {
			if randomFloat() < 0.5 {
				genes = append(genes, g)
			}
		}
		population[i] = &Individual{
			ID:    uuid.New().String(),
			Genes: genes,
		}
	}

	return population
}

// createNextGeneration creates the next generation
func (e *Engine) createNextGeneration(population []*Individual) []*Individual {
	nextGen := make([]*Individual, 0, e.cfg.PopulationSize)

	// Elite selection
	for i := 0; i < e.cfg.EliteCount && i < len(population); i++ {
		nextGen = append(nextGen, population[i].Clone())
	}

	// Generate offspring
	for len(nextGen) < e.cfg.PopulationSize {
		var parent1, parent2 *Individual

		// Tournament selection
		parent1 = e.tournamentSelect(population)
		parent2 = e.tournamentSelect(population)

		// Crossover
		if randomFloat() < e.cfg.CrossoverRate {
			offspring := e.crossover(parent1, parent2)
			// Mutation
			if randomFloat() < e.cfg.MutationRate {
				e.mutate(offspring)
			}
			nextGen = append(nextGen, offspring)
		} else {
			// Clone best parent
			nextGen = append(nextGen, parent1.Clone())
		}
	}

	return nextGen
}

// tournamentSelect selects an individual using tournament selection
func (e *Engine) tournamentSelect(population []*Individual) *Individual {
	tournamentSize := 5
	best := population[randomInt(len(population))]

	for i := 1; i < tournamentSize; i++ {
		candidate := population[randomInt(len(population))]
		if candidate.Fitness > best.Fitness {
			best = candidate
		}
	}

	return best
}

// crossover performs crossover between two individuals
func (e *Engine) crossover(parent1, parent2 *Individual) *Individual {
	child := &Individual{
		ID:    uuid.New().String(),
		Genes: make([]*Gene, 0),
	}

	// Single-point crossover for genes
	for i := 0; i < len(parent1.Genes) || i < len(parent2.Genes); i++ {
		var gene *Gene
		if i%2 == 0 {
			if i < len(parent1.Genes) {
				gene = parent1.Genes[i]
			} else {
				gene = parent2.Genes[i]
			}
		} else {
			if i < len(parent2.Genes) {
				gene = parent2.Genes[i]
			} else {
				gene = parent1.Genes[i]
			}
		}
		if gene != nil {
			child.Genes = append(child.Genes, gene)
		}
	}

	return child
}

// mutate applies mutation to an individual
func (e *Engine) mutate(ind *Individual) {
	for _, gene := range ind.Genes {
		// Random parameter mutation
		for key := range gene.Parameters {
			if randomFloat() < e.cfg.MutationRate {
				gene.Parameters[key] = randomFloat() * 100
			}
		}
	}
}

// sortByFitness sorts population by fitness (descending)
func (e *Engine) sortByFitness(population []*Individual) {
	for i := 0; i < len(population)-1; i++ {
		for j := i + 1; j < len(population); j++ {
			if population[j].Fitness > population[i].Fitness {
				population[i], population[j] = population[j], population[i]
			}
		}
	}
}

// ============================================================================
// Individual
// ============================================================================

// Individual represents an evolved strategy individual
type Individual struct {
	ID            string
	Genes         []*Gene
	Fitness       float64
	Metrics       *PerformanceMetrics
	ConstraintsOK bool
}

type PerformanceMetrics struct {
	SharpeRatio   float64
	MaxDrawdown  float64
	WinRate      float64
	ProfitFactor float64
	TotalReturn  float64
}

// Clone creates a deep copy
func (i *Individual) Clone() *Individual {
	clone := &Individual{
		ID:      uuid.New().String(),
		Fitness: i.Fitness,
		Metrics: i.Metrics,
		Genes:   make([]*Gene, len(i.Genes)),
	}
	for j, g := range i.Genes {
		geneCopy := *g
		clone.Genes[j] = &geneCopy
	}
	return clone
}

// ============================================================================
// Gene Pool
// ============================================================================

// NewGenePool creates a new gene pool
func NewGenePool() *GenePool {
	return &GenePool{
		genes:     make([]*Gene, 0),
		constraint: *NewConstraintChecker(),
	}
}

// Register registers a gene to the pool
func (g *GenePool) Register(gene *Gene) error {
	if g.constraint.Validate(gene) {
		g.genes = append(g.genes, gene)
		return nil
	}
	return fmt.Errorf("gene does not satisfy constraints")
}

// List returns all genes
func (g *GenePool) List() []*Gene {
	return g.genes
}

// Find finds genes by type
func (g *GenePool) Find(geneType GeneType) []*Gene {
	var results []*Gene
	for _, gene := range g.genes {
		if gene.Type == geneType {
			results = append(results, gene)
		}
	}
	return results
}

// ============================================================================
// Constraint Checker
// ============================================================================

// ConstraintChecker validates genes against constraints
type ConstraintChecker struct {
	rules []ConstraintRule
}

// ConstraintRule represents a validation rule
type ConstraintRule struct {
	Name    string
	Message string
	Check   func(*Gene) bool
}

// NewConstraintChecker creates a new constraint checker
func NewConstraintChecker() *ConstraintChecker {
	return &ConstraintChecker{
		rules: []ConstraintRule{
			{
				Name:    "has_name",
				Message: "Gene must have a name",
				Check:   func(g *Gene) bool { return g.Name != "" },
			},
			{
				Name:    "has_code",
				Message: "Gene must have code",
				Check:   func(g *Gene) bool { return g.Code != "" },
			},
		},
	}
}

// Validate validates a gene
func (c *ConstraintChecker) Validate(gene *Gene) bool {
	for _, rule := range c.rules {
		if !rule.Check(gene) {
			fmt.Printf("Constraint failed: %s - %s\n", rule.Name, rule.Message)
			return false
		}
	}
	return true
}

// ============================================================================
// Fitness Evaluator
// ============================================================================

// FitnessEvaluator evaluates individual fitness
type FitnessEvaluator struct {
	weights Weights
}

type Weights struct {
	SharpeWeight   float64
	DrawdownWeight float64
	WinRateWeight  float64
	ProfitWeight   float64
}

// NewFitnessEvaluator creates a new fitness evaluator
func NewFitnessEvaluator() *FitnessEvaluator {
	return &FitnessEvaluator{
		weights: Weights{
			SharpeWeight:   0.3,
			DrawdownWeight: -0.3, // Negative because lower is better
			WinRateWeight:  0.2,
			ProfitWeight:   0.2,
		},
	}
}

// Evaluate evaluates an individual's fitness
func (f *FitnessEvaluator) Evaluate(ind *Individual) float64 {
	if ind.Metrics == nil {
		return 0
	}

	m := ind.Metrics
	return f.weights.SharpeWeight*m.SharpeRatio +
		f.weights.DrawdownWeight*m.MaxDrawdown +
		f.weights.WinRateWeight*m.WinRate +
		f.weights.ProfitWeight*m.TotalReturn
}

// ============================================================================
// Utility Functions
// ============================================================================

func randomFloat() float64 {
	return float64(int(time.Now().UnixNano()%1000)) / 1000.0
}

func randomInt(max int) int {
	if max <= 0 {
		return 0
	}
	return int(time.Now().UnixNano()) % max
}

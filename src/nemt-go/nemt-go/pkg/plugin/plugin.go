// Package plugin provides the plugin system for NEMT
package plugin

import (
	"fmt"
	"plugin"
	"sync"
)

// ============================================================================
// Plugin Manager
// ============================================================================

// Manager manages plugins
type Manager struct {
	plugins map[string]*Plugin
	mu      sync.RWMutex
}

// Plugin represents a loaded plugin
type Plugin struct {
	Name        string
	Version     string
	Description string
	Type        PluginType
	Instance    interface{}
	Symbol      PluginSymbol
}

// PluginSymbol is the plugin interface that must be implemented
type PluginSymbol interface {
	Init() error
	Execute(ctx *Context) error
	GetMetadata() *Metadata
}

// Metadata contains plugin metadata
type Metadata struct {
	Name        string
	Version     string
	Author      string
	Description string
	Dependencies []string
}

// Context provides execution context
type Context struct {
	Config map[string]interface{}
	Data   map[string]interface{}
}

// PluginType represents the type of plugin
type PluginType string

const (
	TypeSignal     PluginType = "signal"
	TypeRisk       PluginType = "risk"
	TypeExecution  PluginType = "execution"
	TypeIndicator  PluginType = "indicator"
	TypeDataSource PluginType = "datasource"
)

// NewManager creates a new plugin manager
func NewManager() *Manager {
	return &Manager{
		plugins: make(map[string]*Plugin),
	}
}

// Register registers a plugin
func (m *Manager) Register(p *Plugin) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	if _, exists := m.plugins[p.Name]; exists {
		return fmt.Errorf("plugin %s already registered", p.Name)
	}

	m.plugins[p.Name] = p
	return nil
}

// Unregister unregisters a plugin
func (m *Manager) Unregister(name string) error {
	m.mu.Lock()
	defer m.mu.Unlock()

	if _, exists := m.plugins[name]; !exists {
		return fmt.Errorf("plugin %s not found", name)
	}

	delete(m.plugins, name)
	return nil
}

// Get returns a plugin by name
func (m *Manager) Get(name string) (*Plugin, bool) {
	m.mu.RLock()
	defer m.mu.RUnlock()
	p, ok := m.plugins[name]
	return p, ok
}

// List returns all registered plugins
func (m *Manager) List() []*Plugin {
	m.mu.RLock()
	defer m.mu.RUnlock()

	plugins := make([]*Plugin, 0, len(m.plugins))
	for _, p := range m.plugins {
		plugins = append(plugins, p)
	}
	return plugins
}

// LoadFromFile loads a plugin from a .so file
func (m *Manager) LoadFromFile(path string) error {
	p, err := plugin.Open(path)
	if err != nil {
		return fmt.Errorf("failed to open plugin: %w", err)
	}

	symPlugin, err := p.Lookup("Plugin")
	if err != nil {
		return fmt.Errorf("failed to find Plugin symbol: %w", err)
	}

	pluginInstance, ok := symPlugin.(PluginSymbol)
	if !ok {
		return fmt.Errorf("plugin does not implement PluginSymbol interface")
	}

	metadata := pluginInstance.GetMetadata()
	pl := &Plugin{
		Name:     metadata.Name,
		Version:  metadata.Version,
		Type:     TypeIndicator, // Would be parsed from metadata
		Instance: pluginInstance,
		Symbol:   pluginInstance,
	}

	if err := pluginInstance.Init(); err != nil {
		return fmt.Errorf("failed to initialize plugin: %w", err)
	}

	return m.Register(pl)
}

// Execute executes a plugin
func (m *Manager) Execute(name string, ctx *Context) error {
	m.mu.RLock()
	defer m.mu.RUnlock()

	p, ok := m.plugins[name]
	if !ok {
		return fmt.Errorf("plugin %s not found", name)
	}

	if p.Symbol == nil {
		return fmt.Errorf("plugin %s has no executable symbol", name)
	}

	return p.Symbol.Execute(ctx)
}

// Package logger provides structured logging for NEMT Gateway
package logger

import (
	"context"
	"encoding/json"
	"fmt"
	"os"
	"time"
)

// Level represents log level
type Level int

const (
	DebugLevel Level = iota
	InfoLevel
	WarnLevel
	ErrorLevel
	FatalLevel
)

var levelNames = map[Level]string{
	DebugLevel: "DEBUG",
	InfoLevel:  "INFO",
	WarnLevel:  "WARN",
	ErrorLevel: "ERROR",
	FatalLevel: "FATAL",
}

// Logger is the application logger
type Logger struct {
	level      Level
	format     string
	outputPath string
}

// LogEntry represents a structured log entry
type LogEntry struct {
	Timestamp string                 `json:"timestamp"`
	Level     string                 `json:"level"`
	Message   string                 `json:"message"`
	Module    string                 `json:"module,omitempty"`
	Fields    map[string]interface{} `json:"fields,omitempty"`
	Error     string                 `json:"error,omitempty"`
}

// ContextKey is the type for context keys
type ContextKey string

const (
	RequestIDKey ContextKey = "request_id"
	UserIDKey    ContextKey = "user_id"
)

// Global logger instance
var defaultLogger *Logger

func init() {
	defaultLogger = New("info", "json", "stdout")
}

// New creates a new logger
func New(level, format, outputPath string) *Logger {
	return &Logger{
		level:      parseLevel(level),
		format:     format,
		outputPath: outputPath,
	}
}

// parseLevel converts string to Level
func parseLevel(level string) Level {
	switch level {
	case "debug":
		return DebugLevel
	case "info":
		return InfoLevel
	case "warn":
		return WarnLevel
	case "error":
		return ErrorLevel
	case "fatal":
		return FatalLevel
	default:
		return InfoLevel
	}
}

// ShouldLog returns true if the given level should be logged
func (l *Logger) ShouldLog(level Level) bool {
	return level >= l.level
}

// Log writes a log entry
func (l *Logger) Log(level Level, msg string, fields map[string]interface{}) {
	if !l.ShouldLog(level) {
		return
	}

	entry := LogEntry{
		Timestamp: time.Now().UTC().Format(time.RFC3339Nano),
		Level:     levelNames[level],
		Message:   msg,
		Fields:    fields,
	}

	if err, ok := fields["error"]; ok {
		entry.Error = fmt.Sprintf("%v", err)
		delete(entry.Fields, "error")
	}

	if module, ok := fields["module"]; ok {
		entry.Module = fmt.Sprintf("%v", module)
		delete(entry.Fields, "module")
	}

	switch l.format {
	case "json":
		l.outputJSON(entry)
	default:
		l.outputText(entry)
	}

	if level == FatalLevel {
		os.Exit(1)
	}
}

// outputJSON writes log entry as JSON
func (l *Logger) outputJSON(entry LogEntry) {
	data, _ := json.Marshal(entry)
	fmt.Fprintln(os.Stdout, string(data))
}

// outputText writes log entry as plain text
func (l *Logger) outputText(entry LogEntry) {
	if entry.Module != "" {
		fmt.Fprintf(os.Stdout, "[%s] [%s] [%s] %s %v\n",
			entry.Timestamp, entry.Level, entry.Module, entry.Message, entry.Fields)
	} else {
		fmt.Fprintf(os.Stdout, "[%s] [%s] %s %v\n",
			entry.Timestamp, entry.Level, entry.Message, entry.Fields)
	}
}

// Debug logs a debug message
func (l *Logger) Debug(msg string, fields ...map[string]interface{}) {
	f := mergeFields(fields)
	l.Log(DebugLevel, msg, f)
}

// Info logs an info message
func (l *Logger) Info(msg string, fields ...map[string]interface{}) {
	f := mergeFields(fields)
	l.Log(InfoLevel, msg, f)
}

// Warn logs a warning message
func (l *Logger) Warn(msg string, fields ...map[string]interface{}) {
	f := mergeFields(fields)
	l.Log(WarnLevel, msg, f)
}

// Error logs an error message
func (l *Logger) Error(msg string, err error, fields ...map[string]interface{}) {
	f := mergeFields(fields)
	if err != nil {
		f["error"] = err.Error()
	}
	l.Log(ErrorLevel, msg, f)
}

// Fatal logs a fatal message and exits
func (l *Logger) Fatal(msg string, err error, fields ...map[string]interface{}) {
	f := mergeFields(fields)
	if err != nil {
		f["error"] = err.Error()
	}
	l.Log(FatalLevel, msg, f)
}

// WithFields creates a new logger with additional default fields
func (l *Logger) WithFields(fields map[string]interface{}) *Logger {
	return &Logger{
		level:      l.level,
		format:     l.format,
		outputPath: l.outputPath,
	}
}

// mergeFields merges field maps
func mergeFields(fields []map[string]interface{}) map[string]interface{} {
	result := make(map[string]interface{})
	for _, f := range fields {
		for k, v := range f {
			result[k] = v
		}
	}
	return result
}

// Package-level convenience functions

// Debug logs a debug message
func Debug(msg string, fields ...map[string]interface{}) {
	defaultLogger.Debug(msg, fields...)
}

// Info logs an info message
func Info(msg string, fields ...map[string]interface{}) {
	defaultLogger.Info(msg, fields...)
}

// Warn logs a warning message
func Warn(msg string, fields ...map[string]interface{}) {
	defaultLogger.Warn(msg, fields...)
}

// Error logs an error message
func Error(msg string, err error, fields ...map[string]interface{}) {
	defaultLogger.Error(msg, err, fields...)
}

// Fatal logs a fatal message and exits
func Fatal(msg string, err error, fields ...map[string]interface{}) {
	defaultLogger.Fatal(msg, err, fields...)
}

// WithContext returns a context with request ID
func WithRequestID(ctx context.Context, requestID string) context.Context {
	return context.WithValue(ctx, RequestIDKey, requestID)
}

// GetRequestID returns request ID from context
func GetRequestID(ctx context.Context) string {
	if requestID, ok := ctx.Value(RequestIDKey).(string); ok {
		return requestID
	}
	return ""
}

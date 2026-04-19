//go:build ignore

package main

import (
	"fmt"
	"io"
	"net/http"
	"strings"
	"time"
)

func main() {
	client := &http.Client{Timeout: 15 * time.Second}
	client.CheckRedirect = func(req *http.Request, via []*http.Request) error {
		// Don't follow redirect - return it as-is
		return http.ErrUseLastResponse
	}

	// Try various YouTube caption APIs
	tests := []struct {
		name string
		url  string
	}{
		{"timedtext json3", "https://youtube.com/api/timedtext?v=dQw4w9WgXcQ&fmt=json3&lang=en"},
		{"timedtext srv3", "https://youtube.com/api/timedtext?v=dQw4w9WgXcQ&fmt=srv3&lang=en"},
		{"transcript API", "https://youtube.com/youtubei/v1/get_transcript?key=AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8&prettyPrint=false"},
		{"player subtitles", "https://www.youtube.com/watch?v=dQw4w9WgXcQ&pbj=1"},
		{"youtubei captions", "https://www.youtube.com/youtubei/v1/get_captions?v=dQw4w9WgXcQ&key=AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8"},
		{"embed page", "https://www.youtube.com/api/timedtext?asr_langs=en&v=dQw4w9WgXcQ&tlang=zh"},
	}

	for _, t := range tests {
		req, _ := http.NewRequest("GET", t.url, nil)
		req.Header.Set("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36")
		req.Header.Set("Accept-Language", "en-US,en;q=0.9")

		resp, err := client.Do(req)
		fmt.Printf("\n[%s]\n  URL: %s\n", t.name, t.url)
		if err != nil {
			fmt.Printf("  Error: %v\n", err)
			continue
		}
		body, _ := io.ReadAll(resp.Body)
		resp.Body.Close()
		fmt.Printf("  Status: %s, Len: %d\n", resp.Status, len(body))
		if len(body) > 0 {
			snippet := strings.TrimSpace(string(body))
			if len(snippet) > 200 {
				snippet = snippet[:200]
			}
			fmt.Printf("  Body: %s\n", snippet)
		}

		// Show redirect location
		for k, v := range resp.Header {
			if strings.ToLower(k) == "location" {
				fmt.Printf("  Redirect: %s\n", v)
			}
		}
	}
}

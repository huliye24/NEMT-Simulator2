package main

import (
	"bytes"
	"context"
	"crypto/hmac"
	csha1 "crypto/sha1"
	"encoding/base64"
	"encoding/xml"
	"flag"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"sync"
	"sync/atomic"
	"time"
)

type Config struct {
	Region    string
	SecretID  string
	SecretKey string
	Bucket    string
}

var cfg Config

var (
	uploaded uint64
	failed   uint64
)

func loadConfig() {
	paths := []string{
		filepath.Join(getExeDir(), "cos_sync.env"),
		filepath.Join(getExeDir(), "..", "cos_sync.env"),
		"cos_sync.env",
	}

	for _, p := range paths {
		if err := loadEnv(p); err == nil {
			break
		}
	}

	cfg = Config{
		Region:    getEnv("COS_REGION", "ap-guangzhou"),
		SecretID:  getEnv("COS_SECRET_ID", ""),
		SecretKey: getEnv("COS_SECRET_KEY", ""),
		Bucket:    getEnv("COS_BUCKET", ""),
	}

	if cfg.SecretID == "" || cfg.SecretKey == "" {
		log.Fatal("[ERROR] Missing COS_SECRET_ID or COS_SECRET_KEY")
	}
}

func loadEnv(path string) error {
	data, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	lines := strings.Split(string(data), "\n")
	for _, line := range lines {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		parts := strings.SplitN(line, "=", 2)
		if len(parts) == 2 {
			os.Setenv(strings.TrimSpace(parts[0]), strings.TrimSpace(parts[1]))
		}
	}
	return nil
}

func getEnv(key, defaultVal string) string {
	if val := os.Getenv(key); val != "" {
		return val
	}
	return defaultVal
}

func getExeDir() string {
	exe, err := os.Executable()
	if err != nil {
		return "."
	}
	return filepath.Dir(exe)
}

func getCOSURL() string {
	return fmt.Sprintf("https://%s.cos.%s.myqcloud.com", cfg.Bucket, cfg.Region)
}

type FileInfo struct {
	Local  string
	Remote string
}

func scanFiles(localDir, remoteDir string) ([]FileInfo, error) {
	var files []FileInfo
	err := filepath.Walk(localDir, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		if !info.IsDir() {
			rel, err := filepath.Rel(localDir, path)
			if err != nil {
				return err
			}
			rel = filepath.ToSlash(rel)
			remote := rel
			if remoteDir != "" {
				remote = strings.TrimSuffix(remoteDir, "/") + "/" + rel
			}
			files = append(files, FileInfo{Local: path, Remote: remote})
		}
		return nil
	})
	return files, err
}

func uploadFile(client *http.Client, file FileInfo) bool {
	ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
	defer cancel()

	f, err := os.Open(file.Local)
	if err != nil {
		atomic.AddUint64(&failed, 1)
		return false
	}
	defer f.Close()

	data, err := io.ReadAll(f)
	if err != nil {
		atomic.AddUint64(&failed, 1)
		return false
	}

	uri := "/" + file.Remote
	now := time.Now().UTC()
	dateStr := now.Format("Mon, 02 Jan 2006 15:04:05 GMT")
	
	// COS v1 signature: Base64(HMAC-SHA1(secretKey, method + path + date))
	// Note: Some COS v1 APIs require Content-Type and Content-Length in signature
	httpString := fmt.Sprintf("PUT\n%s\n\n%d\n%s", uri, len(data), dateStr)
	h := hmac.New(csha1.New, []byte(cfg.SecretKey))
	h.Write([]byte(httpString))
	signature := base64.StdEncoding.EncodeToString(h.Sum(nil))

	auth := fmt.Sprintf("COS %s:%s", cfg.SecretID, signature)

	url := fmt.Sprintf("%s/%s", getCOSURL(), file.Remote)

	req, err := http.NewRequestWithContext(ctx, "PUT", url, bytes.NewReader(data))
	if err != nil {
		atomic.AddUint64(&failed, 1)
		return false
	}

	req.Header.Set("Host", fmt.Sprintf("%s.cos.%s.myqcloud.com", cfg.Bucket, cfg.Region))
	req.Header.Set("Content-Length", fmt.Sprintf("%d", len(data)))
	req.Header.Set("Authorization", auth)
	req.Header.Set("Date", time.Now().UTC().Format(http.TimeFormat))

	resp, err := client.Do(req)
	if err != nil {
		atomic.AddUint64(&failed, 1)
		return false
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 && resp.StatusCode != 201 {
		body, _ := io.ReadAll(resp.Body)
		if atomic.LoadUint64(&failed) < 5 {
			log.Printf("[FAIL] Upload %s: status=%d, body=%s", file.Remote, resp.StatusCode, string(body))
		}
		atomic.AddUint64(&failed, 1)
		return false
	}

	count := atomic.AddUint64(&uploaded, 1)
	if count%100 == 0 {
		fmt.Printf("[PROGRESS] Uploaded: %d, Failed: %d\n", count, atomic.LoadUint64(&failed))
	}
	return true
}

func worker(ctx context.Context, client *http.Client, jobs <-chan FileInfo, wg *sync.WaitGroup) {
	defer wg.Done()
	for {
		select {
		case file, ok := <-jobs:
			if !ok {
				return
			}
			uploadFile(client, file)
		case <-ctx.Done():
			return
		}
	}
}

func syncDir(localDir, remoteDir string, workers int) {
	// Check if localDir is a file or directory
	info, err := os.Stat(localDir)
	if err != nil {
		// Try other paths
		paths := []string{localDir}
		if !filepath.IsAbs(localDir) {
			paths = append(paths,
				filepath.Join(getExeDir(), localDir),
				filepath.Join(getExeDir(), "..", localDir),
			)
		}
		for _, p := range paths {
			if info, err = os.Stat(p); err == nil {
				localDir = p
				break
			}
		}
		if err != nil {
			log.Fatalf("[FAIL] Cannot find '%s': %v", localDir, err)
		}
	}

	var files []FileInfo
	if info.IsDir() {
		files, _ = scanFiles(localDir, remoteDir)
	} else {
		// Single file
		rel := filepath.Base(localDir)
		remote := rel
		if remoteDir != "" {
			remote = remoteDir + "/" + rel
		}
		files = []FileInfo{{Local: localDir, Remote: remote}}
	}

	total := len(files)
	fmt.Printf("[INFO] Total: %d, Workers: %d\n", total, workers)

	jobs := make(chan FileInfo, 10000)
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	var wg sync.WaitGroup
	client := &http.Client{
		Transport: &http.Transport{
			MaxIdleConns:        workers,
			MaxIdleConnsPerHost: workers,
			IdleConnTimeout:     60 * time.Second,
		},
	}

	for i := 0; i < workers; i++ {
		wg.Add(1)
		go worker(ctx, client, jobs, &wg)
	}

	start := time.Now()
	for _, file := range files {
		jobs <- file
	}
	close(jobs)

	wg.Wait()
	elapsed := time.Since(start)

	fmt.Printf("[DONE] Success: %d, Failed: %d, Time: %.1fs\n",
		uploaded, failed, elapsed.Seconds())
}

type ListResp struct {
	Contents []struct {
		Key  string `xml:"Key"`
		Size int64  `xml:"Size"`
	} `xml:"Contents"`
}

func listDir(prefix string) {
	url := getCOSURL() + "/?prefix=" + prefix + "&max-keys=100"

	resp, err := http.Get(url)
	if err != nil {
		fmt.Printf("[FAIL] %v\n", err)
		return
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(resp.Body)
	var result ListResp
	if err := xml.Unmarshal(body, &result); err != nil {
		fmt.Printf("[FAIL] %v\n", err)
		return
	}

	if len(result.Contents) == 0 {
		fmt.Println("[EMPTY]")
		return
	}

	fmt.Printf("\ncos://%s/%s\n", cfg.Bucket, prefix)
	fmt.Println(strings.Repeat("-", 60))
	for _, obj := range result.Contents {
		var s string
		if obj.Size < 1048576 {
			s = fmt.Sprintf("%.1fKB", float64(obj.Size)/1024)
		} else {
			s = fmt.Sprintf("%.1fMB", float64(obj.Size)/1048576)
		}
		fmt.Printf("  %10s  %s\n", s, obj.Key)
	}
	fmt.Println(strings.Repeat("-", 60))
}

func main() {
	flag.Parse()
	loadConfig()

	args := flag.Args()

	if len(args) == 0 {
		listDir("")
		return
	}

	action := args[0]

	if action == "sync" {
		localDir := ""
		remoteDir := ""
		workers := 20

		if len(args) > 1 {
			localDir = args[1]
		}
		if len(args) > 2 {
			remoteDir = args[2]
		}
		if len(args) > 3 {
			workers, _ = strconv.Atoi(args[3])
		}

		if localDir == "" {
			localDir = "."
		}
		syncDir(localDir, remoteDir, workers)
	} else {
		listDir(action)
	}
}

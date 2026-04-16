// Copyright 2026 NEMT Lab
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

// Go Collector - 币安 WebSocket 数据采集器
// 将 BTC/USDT 实时价格写入 Redis Stream
package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/gorilla/websocket"
	"github.com/redis/go-redis/v9"
)

// Binance WebSocket 消息结构
type BinanceTicker struct {
	Symbol     string  `json:"s"` // BTCUSDT
	Price      string  `json:"p"` // 价格变动
	PriceFloat float64 `json:"-"` // 解析后的价格
	Percent    string  `json:"P"` // 24h 涨跌百分比
	Volume     string  `json:"v"` // 成交量
	High       string  `json:"h"` // 24h 最高
	Low        string  `json:"l"` // 24h 最低
	Open       string  `json:"o"` // 24h 开盘
	EventTime  int64   `json:"E"` // 事件时间
}

// K线数据
type BinanceKline struct {
	Symbol     string  `json:"s"`
	Interval   string  `json:"i"`
	OpenTime   int64   `json:"t"`
	Open       float64 `json:"o"`
	High       float64 `json:"h"`
	Low        float64 `json:"l"`
	Close      float64 `json:"c"`
	Volume     float64 `json:"v"`
	CloseTime  int64   `json:"T"`
	EventTime  int64   `json:"E"`
}

var redisClient *redis.Client

func initRedis(addr string) *redis.Client {
	client := redis.NewClient(&redis.Options{
		Addr:     addr,
		Password: "",
		DB:       0,
	})

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if err := client.Ping(ctx).Err(); err != nil {
		log.Printf("⚠️  Redis 连接失败: %v, 将在 5 秒后重试...", err)
		time.Sleep(5 * time.Second)
		os.Exit(1)
	}

	log.Printf("✅ Redis 连接成功: %s", addr)
	return client
}

func writeToRedisStream(ticker *BinanceTicker) error {
	ctx := context.Background()

	data := map[string]interface{}{
		"symbol":     ticker.Symbol,
		"price":      ticker.Price,
		"percent":    ticker.Percent,
		"volume":     ticker.Volume,
		"high":       ticker.High,
		"low":        ticker.Low,
		"open":       ticker.Open,
		"event_time": ticker.EventTime,
	}

	_, err := redisClient.XAdd(ctx, &redis.XAddArgs{
		Stream: "btc_ticker:stream",
		MaxLen: 10000, // 最多保留 10000 条
		Approx: true,
		Values: data,
	}).Result()

	return err
}

func writeKlineToRedis(kline *BinanceKline) error {
	ctx := context.Background()

	data := map[string]interface{}{
		"symbol":     kline.Symbol,
		"interval":   kline.Interval,
		"open_time":  kline.OpenTime,
		"open":       kline.Open,
		"high":       kline.High,
		"low":        kline.Low,
		"close":      kline.Close,
		"volume":     kline.Volume,
		"close_time": kline.CloseTime,
		"event_time": kline.EventTime,
	}

	_, err := redisClient.XAdd(ctx, &redis.XAddArgs{
		Stream: fmt.Sprintf("kline:%s:%s", kline.Symbol, kline.Interval),
		MaxLen: 10000,
		Approx: true,
		Values: data,
	}).Result()

	return err
}

func connectWebSocket() {
	// 币安 WebSocket 端点 - 24h ticker
	url := "wss://stream.binance.com:9443/ws/btcusdt@ticker"

	log.Printf("🔌 正在连接币安 WebSocket: %s", url)

	for {
		conn, _, err := websocket.DefaultDialer.Dial(url, nil)
		if err != nil {
			log.Printf("❌ WebSocket 连接失败: %v, 10秒后重连...", err)
			time.Sleep(10 * time.Second)
			continue
		}

		log.Printf("✅ WebSocket 连接成功!")

		// 保持连接
		for {
			_, message, err := conn.ReadMessage()
			if err != nil {
				log.Printf("❌ 读取消息失败: %v, 重新连接...", err)
				conn.Close()
				break
			}

			var ticker BinanceTicker
			if err := json.Unmarshal(message, &ticker); err != nil {
				continue
			}

			// 解析价格
			var price float64
			fmt.Sscanf(ticker.Price, "%f", &price)

			// 每秒打印一次摘要
			fmt.Printf("\r📊 BTC/USDT: $%s (24h: %s%%) | Vol: %s", ticker.Price, ticker.Percent, ticker.Volume)

			// 异步写入 Redis
			go func(t BinanceTicker) {
				if err := writeToRedisStream(&t); err != nil {
					log.Printf("⚠️ 写入 Redis 失败: %v", err)
				}
			}(ticker)
		}
	}
}

// 订阅 K线 数据
func subscribeKlines(symbol, interval string) {
	url := fmt.Sprintf("wss://stream.binance.com:9443/ws/%s@kline_%s", symbol, interval)

	log.Printf("🔌 订阅 K线: %s %s", symbol, interval)

	for {
		conn, _, err := websocket.DefaultDialer.Dial(url, nil)
		if err != nil {
			log.Printf("❌ K线 WebSocket 连接失败: %v", err)
			time.Sleep(10 * time.Second)
			continue
		}

		log.Printf("✅ K线 WebSocket 连接成功!")

		for {
			_, message, err := conn.ReadMessage()
			if err != nil {
				log.Printf("❌ K线读取失败: %v", err)
				conn.Close()
				break
			}

			// 解析 K线 数据 (格式: [stream, data])
			var rawData []json.RawMessage
			if err := json.Unmarshal(message, &rawData); err != nil {
				continue
			}

			if len(rawData) < 2 {
				continue
			}

			var kline BinanceKline
			if err := json.Unmarshal(rawData[1], &kline); err != nil {
				continue
			}

			log.Printf("📈 K线更新: %s O:%.2f H:%.2f L:%.2f C:%.2f",
				kline.Interval, kline.Open, kline.High, kline.Low, kline.Close)

			go func(k BinanceKline) {
				if err := writeKlineToRedis(&k); err != nil {
					log.Printf("⚠️ K线写入 Redis 失败: %v", err)
				}
			}(kline)
		}
	}
}

func main() {
	log.Println("═══════════════════════════════════════════════")
	log.Println("     🚀 BTC/USDT 数据采集器 v1.0")
	log.Println("═══════════════════════════════════════════════")

	// Redis 地址
	redisAddr := os.Getenv("REDIS_ADDR")
	if redisAddr == "" {
		redisAddr = "redis:6379" // Docker 环境
	}

	// 初始化 Redis
	redisClient = initRedis(redisAddr)

	// 处理优雅退出
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		<-sigChan
		log.Println("\n🛑 收到退出信号，正在关闭...")
		redisClient.Close()
		os.Exit(0)
	}()

	// 启动 WebSocket 连接
	connectWebSocket()
}

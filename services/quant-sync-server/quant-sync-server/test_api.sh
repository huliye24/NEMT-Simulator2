#!/usr/bin/env bash
# Test Obsidian API with curl

API_KEY="2d0057d8d29ba074ad1020700c266e9e5cd1a554de8e8b374e61f48d22591e69"
BASE_URL="https://127.0.0.1:27124"

echo "======================================"
echo "Testing Obsidian API with curl"
echo "======================================"

echo ""
echo "1. List vault files:"
curl -s -k -H "Authorization: Bearer $API_KEY" "$BASE_URL/vault/" | head -c 500

echo ""
echo ""
echo "2. Create a test file:"
curl -s -k -X PUT \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: text/plain" \
  --data "Hello from curl at $(date)" \
  "$BASE_URL/vault/curl-test.md"

echo ""
echo "3. Read back the file:"
curl -s -k -H "Authorization: Bearer $API_KEY" "$BASE_URL/vault/curl-test.md"

echo ""
echo ""
echo "4. Create Chinese content file:"
curl -s -k -X PUT \
  -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: text/plain; charset=utf-8" \
  --data "测试中文内容 - $(date +%Y-%m-%d)" \
  "$BASE_URL/vault/chinese-test.md"

echo ""
echo "5. Read Chinese file:"
curl -s -k -H "Authorization: Bearer $API_KEY" "$BASE_URL/vault/chinese-test.md"

echo ""
echo ""
echo "======================================"
echo "Done"
echo "======================================"

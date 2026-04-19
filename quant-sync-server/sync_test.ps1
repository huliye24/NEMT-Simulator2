$API_KEY = "2d0057d8d29ba074ad1020700c266e9e5cd1a554de8e8b374e61f48d22591e69"
$BASE_URL = "https://127.0.0.1:27124"

add-type @"
    using System.Net;
    using System.Security.Cryptography.X509Certificates;
    public class TrustAllCertsPolicy : ICertificatePolicy {
        public bool CheckValidationResult(ServicePoint s, X509Certificate c, WebRequest r, int p) { return true; }
    }
"@
[System.Net.ServicePointManager]::CertificatePolicy = New-Object TrustAllCertsPolicy

Write-Host "NEMT Obsidian Sync"

$r = Invoke-RestMethod -Uri "$BASE_URL/vault/" -Method Get -Headers @{Authorization = "Bearer $API_KEY"}
Write-Host "Connected. Files: $($r.files.Count)"

Invoke-RestMethod -Uri "$BASE_URL/vault/Architecture/" -Method Post -Headers @{Authorization = "Bearer $API_KEY"} -ErrorAction SilentlyContinue | Out-Null
Invoke-RestMethod -Uri "$BASE_URL/vault/Code/" -Method Post -Headers @{Authorization = "Bearer $API_KEY"} -ErrorAction SilentlyContinue | Out-Null

$headers = @{ Authorization = "Bearer $API_KEY"; "Content-Type" = "text/plain; charset=utf-8" }

$overview = @"
# NEMT Quant OS - Project Overview

Updated: 2026-04-19

## Vision
NEMT = Non-Equilibrium Market Theory
Let strategies survive, compete, and evolve in the market.

## Core Modules
| Module | Status |
|--------|--------|
| NEMT Core | Done |
| 4-Phase State Machine | Done |
| Signal Indicators | Done |
| Risk Management | Done |
| Execution Framework | Done |

## Phases
- [x] Phase 1: Obsidian MCP Integration
- [x] Phase 2: Knowledge Base
- [ ] Phase 3: Kitchen - Architecture
- [ ] Phase 4: Kitchen - Data Layer
"@

$arch = @"
# NEMT Quant OS - Architecture

Updated: 2026-04-19

## Layers
1. Market Layer - Data acquisition
2. NEMT Core - NLS equation
3. Signal Layer - DCI/Vortex
4. Strategy Layer - Multi-strategy
5. Risk Layer - Risk management
6. Execution Layer - Order execution
7. Brain Layer - Decision control
8. Evolution Layer - Strategy culling
"@

Invoke-RestMethod -Uri "$BASE_URL/vault/00-Overview.md" -Method Put -Headers $headers -Body ([System.Text.Encoding]::UTF8.GetBytes($overview))
Write-Host "OK: 00-Overview.md"

Invoke-RestMethod -Uri "$BASE_URL/vault/Architecture/Overview.md" -Method Put -Headers $headers -Body ([System.Text.Encoding]::UTF8.GetBytes($arch))
Write-Host "OK: Architecture/Overview.md"

Write-Host "Done!"

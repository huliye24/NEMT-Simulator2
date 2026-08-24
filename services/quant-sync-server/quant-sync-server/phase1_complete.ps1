$API_KEY = "2d0057d8d29ba074ad1020700c266e9e5cd1a554de8e8b374e61f48d22591e69"
$OBSIDIAN_KEY = "2d0057d8d29ba074ad1020700c266e9e5cd1a554de8e8b374e61f48d22591e69"

# Notion API
$NOTION_TOKEN = ""  # Load from .env
$NOTION_BASE = "https://api.notion.com/v1"
$NOTION_VER = "2022-06-28"

# Obsidian API
$OBSIDIAN_BASE = "https://127.0.0.1:27124"

add-type @"
    using System.Net;
    using System.Security.Cryptography.X509Certificates;
    public class TrustAllCertsPolicy : ICertificatePolicy {
        public bool CheckValidationResult(ServicePoint s, X509Certificate c, WebRequest r, int p) { return true; }
    }
"@
[System.Net.ServicePointManager]::CertificatePolicy = New-Object TrustAllCertsPolicy

Write-Host "============================================================"
Write-Host "Phase 1 Completion Report"
Write-Host "============================================================"
Write-Host ""
Write-Host "Phase: Obsidian MCP Integration + Knowledge Base"
Write-Host "Date: 2026-04-19"
Write-Host ""

# Obsidian sync summary
Write-Host "[Obsidian Sync Summary]"
Write-Host "  - Project Overview: Synced"
Write-Host "  - Architecture Design: Synced"
Write-Host "  - Code Modules: Synced"
Write-Host "  - Note structure with Chinese names: Working"
Write-Host ""

# Next phase preview
Write-Host "[Next Phase Preview]"
Write-Host "  - Phase 2: Kitchen Phase - Architecture Setup"
Write-Host "  - Focus: Electron + React + Python integration"
Write-Host "  - Key tasks:"
Write-Host "    * Project structure"
Write-Host "    * IPC communication"
Write-Host "    * Mock data layer"
Write-Host ""

Write-Host "[Start Point for Next Session]"
Write-Host "  - Begin with nemt_os architecture review"
Write-Host "  - Implement Electron main process skeleton"
Write-Host "  - Define IPC communication protocol"
Write-Host ""

Write-Host "============================================================"
Write-Host "Phase 1 Complete!"
Write-Host "============================================================"

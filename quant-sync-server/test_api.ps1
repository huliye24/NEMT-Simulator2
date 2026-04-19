$API_KEY = "2d0057d8d29ba074ad1020700c266e9e5cd1a554de8e8b374e61f48d22591e69"
$BASE_URL = "https://127.0.0.1:27124"

Write-Host "======================================"
Write-Host "Testing Obsidian API with PowerShell"
Write-Host "======================================"

# Suppress SSL warning
add-type -TypeDefinition @"
    using System.Net;
    using System.Security.Cryptography.X509Certificates;
    public class TrustAllCertsPolicy : ICertificatePolicy {
        public bool CheckValidationResult(
            ServicePoint srvPoint, X509Certificate certificate,
            WebRequest request, int certificateProblem) {
            return true;
        }
    }
"@
[System.Net.ServicePointManager]::CertificatePolicy = New-Object TrustAllCertsPolicy

$headers = @{
    "Authorization" = "Bearer $API_KEY"
}

Write-Host ""
Write-Host "1. List vault files:"
try {
    $response = Invoke-RestMethod -Uri "$BASE_URL/vault/" -Method Get -Headers $headers
    $response.files | ForEach-Object { Write-Host "  $_" }
} catch {
    Write-Host "  Error: $_"
}

Write-Host ""
Write-Host "2. Create test file with Invoke-RestMethod:"
$body = "Hello from PowerShell at $(Get-Date)"
try {
    Invoke-RestMethod -Uri "$BASE_URL/vault/ps-test.md" -Method Put -Headers $headers -Body ([System.Text.Encoding]::UTF8.GetBytes($body)) -ContentType "text/plain"
    Write-Host "  Created ps-test.md"
} catch {
    Write-Host "  Error: $_"
}

Write-Host ""
Write-Host "3. Read back the file:"
try {
    $content = Invoke-RestMethod -Uri "$BASE_URL/vault/ps-test.md" -Method Get -Headers $headers
    Write-Host "  Content: $content"
} catch {
    Write-Host "  Error: $_"
}

Write-Host ""
Write-Host "4. Try with WebClient:"
$wc = New-Object System.Net.WebClient
$wc.Headers.Add("Authorization", "Bearer $API_KEY")
$wc.Encoding = [System.Text.Encoding]::UTF8

Write-Host "  Writing ps-test2.md..."
$content = "Content via WebClient at $(Get-Date)"
$wc.UploadData("$BASE_URL/vault/ps-test2.md", "PUT", [System.Text.Encoding]::UTF8.GetBytes($content))
Write-Host "  Done"

Write-Host "  Reading ps-test2.md..."
try {
    $data = $wc.DownloadData("$BASE_URL/vault/ps-test2.md")
    Write-Host "  Content: $([System.Text.Encoding]::UTF8.GetString($data))"
} catch {
    Write-Host "  Read Error: $_"
}

Write-Host ""
Write-Host "======================================"
Write-Host "Done"
Write-Host "======================================"

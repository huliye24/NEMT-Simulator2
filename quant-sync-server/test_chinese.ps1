$API_KEY = "2d0057d8d29ba074ad1020700c266e9e5cd1a554de8e8b374e61f48d22591e69"
$BASE_URL = "https://127.0.0.1:27124"
$headers = @{
    "Authorization" = "Bearer $API_KEY"
    "Content-Type" = "text/plain"
}

Add-Type @"
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

Write-Host "Test 1: List vault"
$r = Invoke-RestMethod -Uri "$BASE_URL/vault/" -Method Get -Headers $headers
Write-Host "Files:"
$r.files | ForEach-Object { Write-Host "  $_" }

Write-Host ""
Write-Host "Test 2: Create with Chinese filename"
$content = "# Test Chinese"
$path = "测试笔记.md"
try {
    Invoke-RestMethod -Uri "$BASE_URL/vault/$path" -Method Put -Headers $headers -Body ([System.Text.Encoding]::UTF8.GetBytes($content))
    Write-Host "Created: $path"
} catch {
    Write-Host "Error: $_"
}

Write-Host ""
Write-Host "Test 3: Read back"
$r2 = Invoke-RestMethod -Uri "$BASE_URL/vault/测试笔记.md" -Method Get -Headers $headers
Write-Host "Content: $r2"

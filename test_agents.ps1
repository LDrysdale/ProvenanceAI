# Save this as test_agents.ps1

$baseUrl = "http://localhost:8000/ask"

$tests = @(
    @{ message = "hello"; context = "" },
    @{ message = "create a timeline of events"; context = "" },
    @{ message = "send an email to John about the meeting"; context = "" },
    @{ message = "please summarize this article"; context = "" }
)

foreach ($test in $tests) {
    Write-Host "Sending message: $($test.message)"
    $response = curl.exe -X POST $baseUrl -F "message=$($test.message)" -F "context=$($test.context)" --silent
    Write-Host "Response:"
    Write-Host $response
    Write-Host "-----------------------------"
}

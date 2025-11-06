# Simple GitHub Push Setup
# Run this after creating your repository on GitHub

Write-Host "`n" -NoNewline
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "      GitHub Push - Simple Setup        " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Instructions
Write-Host "STEP 1: Create Repository on GitHub" -ForegroundColor Yellow
Write-Host "---------------------------------------" -ForegroundColor Gray
Write-Host "1. Open: " -NoNewline; Write-Host "https://github.com/new" -ForegroundColor Blue
Write-Host "2. Repository name: " -NoNewline; Write-Host "predictive-maintenance-mlops" -ForegroundColor Green
Write-Host "3. Choose Public or Private" -ForegroundColor White
Write-Host "4. " -NoNewline; Write-Host "DO NOT" -ForegroundColor Red -NoNewline; Write-Host " check any initialization options" -ForegroundColor White
Write-Host "5. Click 'Create repository'" -ForegroundColor White
Write-Host ""

$created = Read-Host "Have you created the repository on GitHub? (y/n)"
if ($created -ne 'y') {
    Write-Host "`nPlease create the repository first, then run this script again." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "STEP 2: Enter Your GitHub Details" -ForegroundColor Yellow
Write-Host "---------------------------------------" -ForegroundColor Gray

# Get username
$username = Read-Host "Enter your GitHub username (e.g., john-doe)"
if ([string]::IsNullOrWhiteSpace($username)) {
    Write-Host "Error: Username cannot be empty!" -ForegroundColor Red
    exit 1
}

# Get repo name
Write-Host ""
$repoName = Read-Host "Enter repository name (press Enter for 'predictive-maintenance-mlops')"
if ([string]::IsNullOrWhiteSpace($repoName)) {
    $repoName = "predictive-maintenance-mlops"
}

# Build URL
$githubUrl = "https://github.com/$username/$repoName.git"

Write-Host ""
Write-Host "STEP 3: Confirm Configuration" -ForegroundColor Yellow
Write-Host "---------------------------------------" -ForegroundColor Gray
Write-Host "GitHub Username : " -NoNewline; Write-Host $username -ForegroundColor Green
Write-Host "Repository Name : " -NoNewline; Write-Host $repoName -ForegroundColor Green
Write-Host "Repository URL  : " -NoNewline; Write-Host $githubUrl -ForegroundColor Blue
Write-Host ""

$confirm = Read-Host "Is this correct? (y/n)"
if ($confirm -ne 'y') {
    Write-Host "Cancelled. Please run the script again." -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "STEP 4: Configuring Git Remote" -ForegroundColor Yellow
Write-Host "---------------------------------------" -ForegroundColor Gray

# Check if remote exists
$existingRemote = git remote get-url origin 2>$null
if ($existingRemote) {
    Write-Host "Warning: Remote 'origin' already exists: " -ForegroundColor Yellow -NoNewline
    Write-Host $existingRemote -ForegroundColor White
    git remote remove origin
    Write-Host "Removed old remote." -ForegroundColor Green
}

# Add remote
Write-Host "Adding remote..." -NoNewline
git remote add origin $githubUrl 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host " Done!" -ForegroundColor Green
} else {
    Write-Host " Failed!" -ForegroundColor Red
    Write-Host "Error: Could not add remote. Check if the URL is correct." -ForegroundColor Red
    exit 1
}

# Rename branch
Write-Host "Renaming branch to 'main'..." -NoNewline
git branch -M main 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host " Done!" -ForegroundColor Green
} else {
    Write-Host " Failed!" -ForegroundColor Red
}

Write-Host ""
Write-Host "STEP 5: Push to GitHub" -ForegroundColor Yellow
Write-Host "---------------------------------------" -ForegroundColor Gray
Write-Host ""
Write-Host "IMPORTANT: Authentication" -ForegroundColor Red
Write-Host "When prompted for password, use your " -NoNewline
Write-Host "Personal Access Token" -ForegroundColor Yellow -NoNewline
Write-Host ", NOT your GitHub password!"
Write-Host ""
Write-Host "Don't have a token? Create one here:" -ForegroundColor Cyan
Write-Host "https://github.com/settings/tokens/new" -ForegroundColor Blue
Write-Host ""

$push = Read-Host "Ready to push? (y/n)"
if ($push -ne 'y') {
    Write-Host ""
    Write-Host "No problem! Push later with:" -ForegroundColor Yellow
    Write-Host "  git push -u origin main" -ForegroundColor Cyan
    Write-Host ""
    exit 0
}

Write-Host ""
Write-Host "Pushing to GitHub..." -ForegroundColor Cyan
Write-Host ""

git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "           SUCCESS! 🎉                  " -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Your project is now on GitHub!" -ForegroundColor Green
    Write-Host ""
    Write-Host "View it at:" -ForegroundColor Cyan
    Write-Host "https://github.com/$username/$repoName" -ForegroundColor Blue
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "  • Add repository description on GitHub" -ForegroundColor White
    Write-Host "  • Add topics: mlops, machine-learning, fastapi, python" -ForegroundColor White
    Write-Host "  • Star your own repository ⭐" -ForegroundColor White
    Write-Host "  • Share with others!" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "           Push Failed                  " -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Common issues:" -ForegroundColor Yellow
    Write-Host "1. Wrong username or repository name" -ForegroundColor White
    Write-Host "2. Repository doesn't exist on GitHub" -ForegroundColor White
    Write-Host "3. Used GitHub password instead of Personal Access Token" -ForegroundColor White
    Write-Host "4. No permission to push to this repository" -ForegroundColor White
    Write-Host ""
    Write-Host "Try again:" -ForegroundColor Cyan
    Write-Host "  .\setup_github.ps1" -ForegroundColor White
    Write-Host ""
    Write-Host "Or push manually:" -ForegroundColor Cyan
    Write-Host "  git push -u origin main" -ForegroundColor White
    Write-Host ""
}

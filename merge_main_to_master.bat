@echo off
REM Script to merge all files from main branch to master branch
REM This script handles the merge with unrelated histories

echo ==========================================
echo Merging Main Branch to Master Branch
echo ==========================================
echo.

REM Check if we're in a git repository
if not exist .git (
    echo Error: Not in a git repository!
    exit /b 1
)

REM Fetch all branches
echo Step 1: Fetching all branches...
git fetch origin
if errorlevel 1 (
    echo Failed to fetch branches
    exit /b 1
)
echo √ Branches fetched
echo.

REM Checkout master branch
echo Step 2: Checking out master branch...
git checkout master
if errorlevel 1 (
    echo Failed to checkout master branch
    exit /b 1
)
echo √ On master branch
echo.

REM Show current state
echo Current files on master:
git ls-tree --name-only HEAD
echo.

REM Merge main into master
echo Step 3: Merging main branch into master...
echo Note: This will merge unrelated histories and may have conflicts
echo.

git merge origin/main --allow-unrelated-histories -m "Merge all files from main branch to master branch"
if errorlevel 1 (
    echo Merge has conflicts. Resolving...
    
    REM Resolve README.md conflict by accepting main version
    if exist README.md (
        echo Resolving README.md conflict (using main branch version^)...
        git checkout --theirs README.md
        git add README.md
        echo √ README.md conflict resolved
    )
    
    REM Complete the merge
    git commit -m "Merge all files from main branch to master branch"
    if errorlevel 1 (
        echo Failed to complete merge. Please resolve conflicts manually.
        exit /b 1
    )
    echo √ Merge completed with conflict resolution
) else (
    echo √ Merge completed successfully!
)

echo.
echo Step 4: Verifying merge...
echo Total files now on master:
git ls-tree -r --name-only HEAD | find /c /v ""
echo.

echo Files added from main branch:
git diff --name-only origin/master HEAD
echo.

REM Push to remote
echo Step 5: Pushing to remote master branch...
set /p push="Do you want to push to remote? (y/n) "

if /i "%push%"=="y" (
    git push origin master
    if errorlevel 1 (
        echo Failed to push to remote
        exit /b 1
    )
    echo √ Successfully pushed to remote master branch!
    echo.
    echo ==========================================
    echo Merge Complete!
    echo ==========================================
    echo.
    echo All files from main branch are now on master branch.
    echo You can verify by running:
    echo   git checkout master
    echo   git ls-tree -r --name-only HEAD
) else (
    echo.
    echo Merge completed locally but not pushed to remote.
    echo To push later, run:
    echo   git push origin master
)

echo.
echo Done!

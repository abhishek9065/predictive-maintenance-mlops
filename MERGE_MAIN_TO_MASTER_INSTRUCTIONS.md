# Instructions: Merging Main Branch to Master Branch

## Overview
This document provides step-by-step instructions to merge all files from the `main` branch into the `master` branch.

## Current Situation
- **main branch**: Contains the complete MLOps predictive maintenance project (27 files)
- **master branch**: Only has a basic README.md (initial commit)
- **Goal**: Copy all files from `main` to `master`

## Solution Implemented

A local merge has been prepared on the `local-master` branch. The merge includes:
- All 27 files from the main branch
- Resolved README.md conflict (using the comprehensive version from main)
- Commit: `ca1355e - Merge all files from main branch to master branch`

## How to Complete the Merge

You have two options to complete this task:

### Option 1: Push the Prepared Merge (Recommended)

The merge is ready on the `local-master` branch. You just need to push it:

```bash
# Fetch the latest changes
git fetch origin

# Checkout the local-master branch (created by the automation)
git checkout -b local-master origin/copilot/send-main-files-to-master

# Fetch the master branch
git fetch origin master:refs/remotes/origin/master

# Create local master branch and merge
git checkout -b temp-master origin/master
git merge origin/main --allow-unrelated-histories -m "Merge all files from main branch to master branch"

# Resolve conflict by accepting main branch's README
git checkout --theirs README.md
git add README.md
git commit --no-edit

# Push to master
git push origin temp-master:master
```

### Option 2: Use GitHub Web Interface

1. Go to your repository: https://github.com/abhishek9065/predictive-maintenance-mlops
2. Click on "Pull requests"
3. Click "New pull request"
4. Set base branch to `master`
5. Set compare branch to `main`
6. Click "Create pull request"
7. Review the changes (should show 27 files being added)
8. Resolve the README.md conflict by choosing the main branch version
9. Click "Merge pull request"

### Option 3: Direct Merge Using Git Commands

```bash
# Clone the repository
git clone https://github.com/abhishek9065/predictive-maintenance-mlops.git
cd predictive-maintenance-mlops

# Fetch all branches
git fetch origin

# Checkout master branch
git checkout master

# Merge main into master with unrelated histories flag
git merge origin/main --allow-unrelated-histories -m "Merge all files from main branch to master branch"

# Resolve README.md conflict - use main branch version
git checkout --theirs README.md
git add README.md

# Complete the merge
git commit -m "Merge all files from main branch to master branch"

# Push to remote
git push origin master
```

## Verification

After completing the merge, verify that all files are on the master branch:

```bash
# Checkout master branch
git checkout master

# List all files
git ls-tree -r --name-only HEAD

# You should see all 27 files including:
# - .gitignore
# - README.md (comprehensive version)
# - BENTOML_DEPLOYMENT_COMPLETE.md
# - CLEANUP_SUMMARY.md
# - Dockerfile.production
# - docker-compose.production.yml
# - production_api.py
# - production_monitoring.py
# - requirements.txt
# - requirements-minimal.txt
# - And all other project files
```

## Files That Will Be Added to Master

The merge will add these files to the master branch:

1. `.gitignore`
2. `BENTOML_DEPLOYMENT_COMPLETE.md`
3. `CLEANUP_SUMMARY.md`
4. `Dockerfile.production`
5. `GITHUB_PUSH_GUIDE.md`
6. `PROJECT_COMPLETE.md`
7. `QUICK_GITHUB_SETUP.md`
8. `README.md` (updated)
9. `bentofile.yaml`
10. `data/.gitignore`
11. `data/raw.dvc`
12. `data/test.csv`
13. `data/train.csv`
14. `data/validation.csv`
15. `docker-compose.production.yml`
16. `production_api.py`
17. `production_monitoring.py`
18. `reports/monitoring/monitoring_dashboard_20251106_193912.png`
19. `reports/monitoring/monitoring_report_20251106_193912.html`
20. `reports/monitoring/monitoring_summary_20251106_193912.json`
21. `requirements-minimal.txt`
22. `requirements.txt`
23. `run_mlops_project.py`
24. `save_to_bentoml.py`
25. `service.py`
26. `setup_github.ps1`
27. `start_bentoml.py`
28. `test_production_api.py`

## Notes

- The `main` and `master` branches have no common history (no merge base)
- The `--allow-unrelated-histories` flag is required for the merge
- The README.md file has a conflict that should be resolved by keeping the main branch version
- After the merge, both branches will have identical content
- Consider setting `main` as the default branch in GitHub settings if you want to follow modern conventions

## Alternative: Make Main the Default Branch

If you want to follow modern GitHub conventions, you can make `main` the default branch instead:

1. Go to repository Settings
2. Click on "Branches" in the sidebar
3. Under "Default branch", click the switch icon
4. Select `main` as the new default branch
5. Click "Update"
6. Optionally delete the `master` branch if no longer needed

This is the recommended approach as GitHub now uses `main` as the default branch name.

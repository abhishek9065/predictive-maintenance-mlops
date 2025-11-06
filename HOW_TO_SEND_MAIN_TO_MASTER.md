# How to Send All Files from Main to Master Branch

This guide provides multiple methods to transfer all files from the `main` branch to the `master` branch.

## Quick Summary

**Current State:**
- `main` branch: 27 files (complete MLOps project)
- `master` branch: 1 file (basic README.md)

**Goal:** Merge all files from `main` to `master`

---

## Method 1: Automated Script (Easiest) ⭐

We've created scripts to automate the entire process.

### On Linux/Mac:
```bash
./merge_main_to_master.sh
```

### On Windows:
```batch
merge_main_to_master.bat
```

The script will:
1. Fetch all branches
2. Checkout master branch
3. Merge main into master
4. Resolve conflicts automatically
5. Ask if you want to push to remote
6. Push changes if confirmed

---

## Method 2: Manual Git Commands

### Step-by-Step Instructions:

```bash
# 1. Fetch all branches
git fetch origin

# 2. Checkout master branch
git checkout master

# 3. Merge main into master (with unrelated histories flag)
git merge origin/main --allow-unrelated-histories -m "Merge all files from main branch to master branch"

# 4. Resolve README.md conflict (use main branch version)
git checkout --theirs README.md
git add README.md

# 5. Complete the merge
git commit -m "Merge all files from main branch to master branch"

# 6. Push to remote
git push origin master
```

---

## Method 3: GitHub Web Interface

This is the safest method if you're not comfortable with Git commands.

### Steps:

1. **Go to your repository:**
   ```
   https://github.com/abhishek9065/predictive-maintenance-mlops
   ```

2. **Create a Pull Request:**
   - Click "Pull requests" tab
   - Click "New pull request"
   - Set **base:** `master`
   - Set **compare:** `main`
   - Click "Create pull request"

3. **Review Changes:**
   - You should see 27 files being added/modified
   - Review the changes to ensure everything looks correct

4. **Resolve Conflicts:**
   - If there's a conflict in README.md:
     - Click "Resolve conflicts"
     - Choose the version from `main` branch (the longer, comprehensive one)
     - Mark as resolved

5. **Merge the PR:**
   - Click "Merge pull request"
   - Click "Confirm merge"
   - Done! ✅

---

## Method 4: Using Git GUI Tools

If you prefer visual tools:

### GitHub Desktop:
1. Open the repository in GitHub Desktop
2. Switch to `master` branch
3. Click "Branch" → "Merge into current branch"
4. Select `main` branch
5. Click "Merge"
6. Resolve conflicts if any
7. Push to remote

### GitKraken / SourceTree:
1. Open the repository
2. Checkout `master` branch
3. Right-click on `main` branch
4. Select "Merge main into master"
5. Resolve conflicts
6. Push changes

---

## Verification

After merging, verify that all files are on master:

```bash
# Switch to master branch
git checkout master

# List all files
git ls-tree -r --name-only HEAD

# Count files (should be 28)
git ls-tree -r --name-only HEAD | wc -l
```

You should see all these files on master:
- `.gitignore`
- `BENTOML_DEPLOYMENT_COMPLETE.md`
- `CLEANUP_SUMMARY.md`
- `Dockerfile.production`
- `GITHUB_PUSH_GUIDE.md`
- `PROJECT_COMPLETE.md`
- `QUICK_GITHUB_SETUP.md`
- `README.md` (updated to comprehensive version)
- `bentofile.yaml`
- `docker-compose.production.yml`
- `production_api.py`
- `production_monitoring.py`
- `requirements.txt`
- `requirements-minimal.txt`
- `run_mlops_project.py`
- `save_to_bentoml.py`
- `service.py`
- `setup_github.ps1`
- `start_bentoml.py`
- `test_production_api.py`
- Plus all files in `data/` and `reports/` directories

---

## Troubleshooting

### Issue: "no merge base" error
**Solution:** Use `--allow-unrelated-histories` flag
```bash
git merge origin/main --allow-unrelated-histories
```

### Issue: Conflict in README.md
**Solution:** Accept the main branch version (it's more comprehensive)
```bash
git checkout --theirs README.md
git add README.md
```

### Issue: Authentication failed when pushing
**Solution:** 
1. Check your Git credentials
2. Use SSH instead of HTTPS
3. Or merge via GitHub web interface

### Issue: Already up to date (but files not transferred)
**Solution:** Make sure you're on the master branch
```bash
git checkout master
git merge origin/main --allow-unrelated-histories
```

---

## Alternative Recommendation

Instead of merging into master, consider making `main` the default branch:

### Why?
- GitHub now uses `main` as the default branch name
- Your project work is already on `main`
- Follows modern conventions
- No need to merge

### How to Make Main the Default:
1. Go to repository **Settings**
2. Click **Branches**
3. Under "Default branch", click the switch icon
4. Select `main`
5. Click "Update"
6. Optionally delete `master` branch

This is the **recommended approach** for modern GitHub repositories.

---

## Need Help?

If you encounter any issues:
1. Check the detailed instructions in `MERGE_MAIN_TO_MASTER_INSTRUCTIONS.md`
2. Review Git status: `git status`
3. Check branch differences: `git diff master main`
4. View commit history: `git log --oneline --graph --all`

---

## Summary

**Recommended Method:** Use the automated script (`merge_main_to_master.sh` or `.bat`)

**Alternative:** Use GitHub web interface for safety

**Best Practice:** Make `main` the default branch instead of merging

Choose the method you're most comfortable with! 🚀

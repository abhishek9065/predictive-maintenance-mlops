# 🚀 Quick Start: Merge Main to Master

## What This PR Does

This PR provides **automated tools and comprehensive documentation** to help you transfer all files from the `main` branch to the `master` branch.

---

## ⚡ Quick Start (Choose One Method)

### Option 1: Automated Script (Recommended) ⭐

**On Linux/Mac:**
```bash
chmod +x merge_main_to_master.sh
./merge_main_to_master.sh
```

**On Windows:**
```batch
merge_main_to_master.bat
```

That's it! The script handles everything automatically.

---

### Option 2: GitHub Web Interface (Safest)

1. Go to: https://github.com/abhishek9065/predictive-maintenance-mlops/compare/master...main
2. Click "Create pull request"
3. Review the 27 files being added
4. If there's a README conflict, choose the `main` version
5. Click "Merge pull request"
6. Done! ✅

---

### Option 3: Manual Git Commands

```bash
git fetch origin
git checkout master
git merge origin/main --allow-unrelated-histories -m "Merge all files from main to master"
git checkout --theirs README.md  # Resolve conflict
git add README.md
git commit -m "Merge all files from main to master"
git push origin master
```

---

## 📚 Full Documentation

- **[HOW_TO_SEND_MAIN_TO_MASTER.md](HOW_TO_SEND_MAIN_TO_MASTER.md)** - Complete guide with 4 methods
- **[MERGE_MAIN_TO_MASTER_INSTRUCTIONS.md](MERGE_MAIN_TO_MASTER_INSTRUCTIONS.md)** - Detailed technical instructions

---

## 📦 What Gets Transferred

All **27 files** from `main` to `master`, including:

- Complete MLOps project files
- Production-ready API (`production_api.py`)
- Monitoring system (`production_monitoring.py`)
- Docker configuration
- BentoML deployment files
- Training data and models
- Comprehensive documentation
- And more...

---

## 🎯 Current Status

| Branch | Files | Status |
|--------|-------|--------|
| **main** | 27 files | ✅ Complete MLOps project |
| **master** | 1 file | 📝 Basic README only |
| **Goal** | Copy all | 🎯 Transfer everything |

---

## 💡 Alternative Recommendation

Instead of merging to master, consider **making `main` the default branch**:

1. Go to Repository **Settings** → **Branches**
2. Change default branch from `master` to `main`
3. Click "Update"

**Why?** 
- GitHub's modern convention
- Your work is already on `main`
- No merge needed!

---

## ✅ Verification

After merging, verify with:

```bash
git checkout master
git ls-tree -r --name-only HEAD | wc -l  # Should show 28
```

---

## 🆘 Need Help?

Check the documentation files or review:
- File list: See `MERGE_MAIN_TO_MASTER_INSTRUCTIONS.md`
- Troubleshooting: See `HOW_TO_SEND_MAIN_TO_MASTER.md`

---

## 🎉 Summary

**Files Provided in This PR:**
1. ✅ `merge_main_to_master.sh` - Automated bash script
2. ✅ `merge_main_to_master.bat` - Automated Windows script  
3. ✅ `HOW_TO_SEND_MAIN_TO_MASTER.md` - Quick guide (4 methods)
4. ✅ `MERGE_MAIN_TO_MASTER_INSTRUCTIONS.md` - Detailed technical guide

**Next Step:** Choose your preferred method and execute!

---

**Ready to go?** Pick a method above and transfer your files! 🚀

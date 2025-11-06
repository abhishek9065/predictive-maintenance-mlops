# 🚀 Quick GitHub Setup - 5 Minutes

## 📝 What You Need

1. A GitHub account (create one at https://github.com/join if needed)
2. Your MLOps project (✅ Already ready!)
3. 5 minutes

---

## 🎯 Step-by-Step Guide

### Step 1: Create GitHub Repository (2 minutes)

1. **Open this link in your browser:**
   ```
   https://github.com/new
   ```

2. **Fill in the form:**
   - **Repository name:** `predictive-maintenance-mlops`
   - **Description:** "MLOps pipeline for predictive maintenance with monitoring"
   - **Public** or **Private** (your choice)
   - ⚠️ **IMPORTANT:** Leave all checkboxes **UNCHECKED**
     - ❌ Do NOT add README
     - ❌ Do NOT add .gitignore
     - ❌ Do NOT add license

3. **Click "Create repository"** button (green button at bottom)

4. **You'll see a page with instructions** - keep this page open!

---

### Step 2: Get Your GitHub Username (30 seconds)

Your GitHub username is in the URL when you're on GitHub:
```
https://github.com/YOUR_USERNAME
                    ^^^^^^^^^^^^
                    This is your username
```

**Example:**
- If you see `https://github.com/john-doe`, your username is `john-doe`

---

### Step 3: Run Setup Script (2 minutes)

**In PowerShell (in your project folder):**

```powershell
.\setup_github.ps1
```

The script will ask you:
1. ✅ "Have you created the repository?" → Type `y` and press Enter
2. ✅ "Enter your GitHub username" → Type your username and press Enter
3. ✅ "Enter repository name" → Just press Enter (uses default)
4. ✅ "Is this correct?" → Type `y` and press Enter
5. ✅ "Ready to push?" → Type `y` and press Enter

---

### Step 4: Authenticate (1 minute)

When Git asks for credentials:

**Username:** `your-github-username`

**Password:** Use **Personal Access Token** (NOT your GitHub password!)

#### 🔑 How to Get Personal Access Token:

**Quick method:**
1. Go to: https://github.com/settings/tokens/new
2. Note: "MLOps Project"
3. Expiration: 90 days (or your choice)
4. Select scope: Check **repo** (full control of private repositories)
5. Click "Generate token" (green button at bottom)
6. **Copy the token** (you'll only see it once!)
7. **Paste it as the password** when Git asks

---

### Step 5: Done! 🎉

After successful push, your project will be at:
```
https://github.com/YOUR_USERNAME/predictive-maintenance-mlops
```

---

## 🎬 Alternative: Manual Commands

If you prefer to do it manually:

```bash
# 1. Add GitHub remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/predictive-maintenance-mlops.git

# 2. Rename branch to main
git branch -M main

# 3. Push to GitHub
git push -u origin main
```

---

## 🆘 Troubleshooting

### "Repository not found"
- ✅ Make sure you created the repository on GitHub
- ✅ Check your username is correct
- ✅ Verify repository name matches exactly

### "Authentication failed"
- ✅ Use **Personal Access Token**, not your password
- ✅ Token needs **repo** scope
- ✅ Make sure you copied the entire token

### "Permission denied"
- ✅ Check you're the owner of the repository
- ✅ Verify token has correct permissions

### "Remote already exists"
```bash
# Remove old remote and try again
git remote remove origin
.\setup_github.ps1
```

---

## 📊 What Gets Pushed

```
✅ All Python code (120 files)
✅ Documentation (README, guides)
✅ Docker & Kubernetes configs
✅ Training data & models
✅ Monitoring reports
✅ BentoML configuration
✅ Everything needed to run the project!
```

---

## 🎯 After Pushing

### Make Your Repo Look Professional:

1. **Add Description**
   - Go to your repository
   - Click ⚙️ (gear icon) next to "About"
   - Add: "End-to-end MLOps pipeline for predictive maintenance"

2. **Add Topics**
   Click "Add topics" and add:
   - `mlops`
   - `machine-learning`
   - `fastapi`
   - `python`
   - `predictive-maintenance`
   - `bentoml`
   - `monitoring`

3. **Star Your Repo** ⭐
   Click the "Star" button on your repo!

---

## 🚀 Quick Commands Reference

```bash
# Check current status
git status

# View remote
git remote -v

# View commit history
git log --oneline -5

# Future updates
git add .
git commit -m "Your update message"
git push
```

---

## 📞 Need Help?

- **Script not working?** Run: `Get-ExecutionPolicy` 
  - If "Restricted", run: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`
  
- **Git not found?** Install Git: https://git-scm.com/download/win

- **Still stuck?** Check: `GITHUB_PUSH_GUIDE.md` for detailed docs

---

## ✅ Summary

1. Create repo on GitHub: https://github.com/new
2. Run: `.\setup_github.ps1`
3. Enter your username
4. Use Personal Access Token when prompted
5. Done! 🎉

**That's it! Your MLOps project will be live on GitHub!**

---

**Ready? Start with Step 1 above! ⬆️**

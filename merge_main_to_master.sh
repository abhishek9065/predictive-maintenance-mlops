#!/bin/bash

# Script to merge all files from main branch to master branch
# This script handles the merge with unrelated histories

set -e  # Exit on error

echo "=========================================="
echo "Merging Main Branch to Master Branch"
echo "=========================================="
echo ""

# Check if we're in a git repository
if [ ! -d .git ]; then
    echo "Error: Not in a git repository!"
    exit 1
fi

# Fetch all branches
echo "Step 1: Fetching all branches..."
git fetch origin
echo "✓ Branches fetched"
echo ""

# Checkout master branch
echo "Step 2: Checking out master branch..."
git checkout master
echo "✓ On master branch"
echo ""

# Show current state
echo "Current files on master:"
git ls-tree --name-only HEAD
echo ""

# Merge main into master
echo "Step 3: Merging main branch into master..."
echo "Note: This will merge unrelated histories and may have conflicts"
echo ""

if git merge origin/main --allow-unrelated-histories -m "Merge all files from main branch to master branch"; then
    echo "✓ Merge completed successfully!"
else
    echo "Merge has conflicts. Resolving..."
    
    # Resolve README.md conflict by accepting main version
    if [ -f README.md ]; then
        echo "Resolving README.md conflict (using main branch version)..."
        git checkout --theirs README.md
        git add README.md
        echo "✓ README.md conflict resolved"
    fi
    
    # Check if there are other conflicts
    if git diff --name-only --diff-filter=U | grep -q .; then
        echo "⚠ Warning: There are other unresolved conflicts:"
        git diff --name-only --diff-filter=U
        echo ""
        echo "Please resolve these conflicts manually and run:"
        echo "  git add <resolved-files>"
        echo "  git commit"
        exit 1
    fi
    
    # Complete the merge
    git commit -m "Merge all files from main branch to master branch"
    echo "✓ Merge completed with conflict resolution"
fi

echo ""
echo "Step 4: Verifying merge..."
echo "Total files now on master:"
git ls-tree -r --name-only HEAD | wc -l
echo ""

echo "Files added from main branch:"
git diff --name-only origin/master HEAD
echo ""

# Push to remote
echo "Step 5: Pushing to remote master branch..."
read -p "Do you want to push to remote? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    git push origin master
    echo "✓ Successfully pushed to remote master branch!"
    echo ""
    echo "=========================================="
    echo "Merge Complete!"
    echo "=========================================="
    echo ""
    echo "All files from main branch are now on master branch."
    echo "You can verify by running:"
    echo "  git checkout master"
    echo "  git ls-tree -r --name-only HEAD"
else
    echo ""
    echo "Merge completed locally but not pushed to remote."
    echo "To push later, run:"
    echo "  git push origin master"
fi

echo ""
echo "Done!"

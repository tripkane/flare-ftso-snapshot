#!/usr/bin/env python3
"""
Quick script to simplify the main dashboard by replacing it with the working version
"""
import shutil
import os

# Copy the working fixed dashboard over the main index.html
src = r"c:\Users\tripk\Dropbox\Documents\github\flare-ftso-snapshot\docs\fixed-dashboard.html"
dst = r"c:\Users\tripk\Dropbox\Documents\github\flare-ftso-snapshot\docs\index.html"

# Backup the original
backup = r"c:\Users\tripk\Dropbox\Documents\github\flare-ftso-snapshot\docs\index-backup.html"
if os.path.exists(dst):
    shutil.copy2(dst, backup)
    print(f"✅ Backed up original to {backup}")

# Copy the working version
shutil.copy2(src, dst)
print(f"✅ Replaced index.html with working fixed dashboard")
print("🚀 Main dashboard should now work at http://localhost:8000/")

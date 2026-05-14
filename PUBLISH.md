# Publishing CreatorAgent to GitHub

The repo is fully prepared and committed. Follow these steps to publish it.

## 📋 Step 1: Create the GitHub Repo

1. Go to **https://github.com/new**
2. Repository name: `creatoragent`
3. Description: `God-tier AI solution architect & builder CLI — multi-provider, multi-domain`
4. Choose **Public** (so others can install it)
5. **Do NOT** check "Initialize with README" (we already have one)
6. Click **Create repository**

## 📋 Step 2: Push Your Code

Replace `YOUR_USERNAME` with your actual GitHub username:

```bash
cd ~/.workspace/creatoragent

# Add your GitHub repo as the remote
git remote add origin https://github.com/YOUR_USERNAME/creatoragent.git

# Push the main branch
git push -u origin main
```

If you have 2FA enabled, use a [Personal Access Token](https://github.com/settings/tokens) instead of your password when prompted.

## 📋 Step 3: Update Placeholders

The README and install script have `YOUR_USERNAME` placeholders. Replace them:

```bash
# On Linux/Mac:
sed -i 's/YOUR_USERNAME/your-actual-username/g' README.md install.sh CONTRIBUTING.md

# Then commit:
git add -A
git commit -m "Update GitHub username"
git push
```

## 📋 Step 4: Create Your First Release

This triggers GitHub Actions to auto-build the Linux/Windows/macOS binaries:

```bash
git tag v1.0.0
git push origin v1.0.0
```

In ~10 minutes, GitHub will:
1. Build the Linux binary + .deb
2. Build the Windows .exe + .zip
3. Build macOS .dmg for both Intel and Apple Silicon
4. Create a GitHub Release with all artifacts attached

You can watch the progress at:
`https://github.com/YOUR_USERNAME/creatoragent/actions`

## 📋 Step 5: Share It!

Once your release is published, anyone can install with:

### One-line install (Linux/Mac)
```bash
curl -fsSL https://raw.githubusercontent.com/YOUR_USERNAME/creatoragent/main/install.sh | bash
```

### Via pip
```bash
pip install "creatoragent[all] @ git+https://github.com/YOUR_USERNAME/creatoragent.git"
```

### Direct binary download
Go to `https://github.com/YOUR_USERNAME/creatoragent/releases/latest`

## 🌟 Step 6: (Optional) Make It Official

Once you have some users:

### Publish to PyPI
```bash
pip install build twine
python -m build
twine upload dist/*
# Now: pip install creatoragent
```

### Create a Homebrew tap (macOS users)
```bash
# Create a separate repo: homebrew-tap
# Add a Formula: creatoragent.rb
# Now: brew install YOUR_USERNAME/tap/creatoragent
```

### Submit to Snap Store (Linux users)
```bash
snapcraft init
snapcraft register creatoragent
snapcraft upload --release=stable
# Now: snap install creatoragent
```

## 🔧 Updating the Repo Later

```bash
# Make changes
git add .
git commit -m "Add new feature"
git push

# Release new version
# Update version in pyproject.toml first, then:
git tag v1.1.0
git push origin v1.1.0
```

## 🆘 Troubleshooting

**"Permission denied" when pushing**
- Use a [Personal Access Token](https://github.com/settings/tokens)
- Or set up [SSH keys](https://docs.github.com/en/authentication/connecting-to-github-with-ssh)

**Actions not running**
- Make sure the repo is public, OR you're on a paid plan
- Check that workflow permissions allow writing (Settings → Actions → Workflow permissions → Read and write)

**Release builds fail**
- Check `https://github.com/YOUR_USERNAME/creatoragent/actions` for the error log
- The most common issue is missing tag — make sure you tagged with `v` prefix (e.g. `v1.0.0`, not `1.0.0`)

---

**Ready to publish?** The repo is committed and ready. Just create the GitHub repo and push! 🚀

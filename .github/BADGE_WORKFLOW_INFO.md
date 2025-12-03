# Badge Workflow Information

## Why is `badge.yml` disabled?

The badge workflow (`badge.yml.disabled`) is disabled by default because it requires additional setup with GitHub secrets. Without these secrets, the workflow would fail on every run.

## Do I need it?

**No!** The badge workflow is completely optional.

The main `tests.yml` workflow already provides:
- ✅ Test status visible in Actions tab
- ✅ Status checks on pull requests
- ✅ Green checkmark/red X on commits
- ✅ GitHub Actions badge in README

The badge workflow only adds:
- 🎨 A customizable dynamic badge
- 📊 Custom badge styling options

## What's the difference?

### Built-in GitHub Actions Badge (Included)
```markdown
![Tests](https://github.com/joshmiller83/pdf2txt/actions/workflows/tests.yml/badge.svg)
```
Shows: `passing` / `failing` with green/red colors
Updates: Automatically based on workflow status
Setup: None required ✅

### Dynamic Badge (Optional - Disabled)
```markdown
![Tests](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/...)
```
Shows: Custom message and colors
Updates: Via badge.yml workflow
Setup: Requires GitHub Gist and Personal Access Token ⚠️

## Should I enable it?

**You probably don't need it.** Only enable if you:
- Want to customize badge appearance beyond the default
- Already have GitHub Gist setup for badges
- Enjoy tinkering with CI/CD workflows

## How to enable it

If you really want to enable the dynamic badge:

1. **Create a GitHub Gist**
   - Visit https://gist.github.com
   - Create new public gist named `pdf2txt-tests.json`
   - Content: `{}`

2. **Create Personal Access Token**
   - GitHub Settings → Developer Settings → Personal Access Tokens
   - Create token with `gist` scope

3. **Add Repository Secrets**
   - Repository Settings → Secrets and Variables → Actions
   - Add `GIST_SECRET` with your token
   - Add `BADGE_GIST_ID` with your gist ID

4. **Enable the workflow**
   ```bash
   mv .github/workflows/badge.yml.disabled .github/workflows/badge.yml
   git add .github/workflows/badge.yml
   git commit -m "Enable badge workflow"
   git push
   ```

## Troubleshooting

### Workflow fails with "404 Not Found"
This means the secrets aren't configured. The workflow is now disabled by default to prevent this error.

### I don't want this file
You can safely delete `badge.yml.disabled` if you're sure you won't use it:
```bash
rm .github/workflows/badge.yml.disabled
```

The main testing workflow will continue to work perfectly without it.

## Summary

- ✅ **Main workflow (`tests.yml`)**: Active and working
- ⏸️ **Badge workflow (`badge.yml.disabled`)**: Disabled, optional
- 🎯 **Recommendation**: Keep badge workflow disabled unless you have a specific need for it

The GitHub Actions badge in your README already provides everything most users need!

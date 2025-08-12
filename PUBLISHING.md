# Publishing Guide

This guide explains how to publish `pydantic-typed-cache` to PyPI using GitHub Actions with OIDC (Trusted Publisher).

## Setup PyPI Trusted Publisher

### 1. For PyPI (Production)

1. Go to [PyPI.org](https://pypi.org) and login
2. Navigate to "Your projects" → "Publishing"
3. Add a new pending publisher with these settings:
   - **PyPI Project Name**: `pydantic-typed-cache`
   - **Owner**: `mom-mom`
   - **Repository name**: `pydantic-cache`
   - **Workflow name**: `publish.yml`
   - **Environment name**: `pypi` (optional but recommended)

### 2. For TestPyPI (Testing)

1. Go to [TestPyPI.org](https://test.pypi.org) and login
2. Follow the same steps with:
   - **Workflow name**: `publish-test.yml`
   - **Environment name**: `testpypi`

## Publishing Process

### Automatic Publishing to TestPyPI

TestPyPI publishing is triggered automatically when:
- Changes are pushed to `main` branch
- Files in `pyproject.toml` or `pydantic_cache/` are modified

Or manually trigger via GitHub Actions UI.

### Publishing to PyPI

1. **Update version** in `pyproject.toml`
2. **Commit and push** changes:
   ```bash
   git add pyproject.toml
   git commit -m "chore: bump version to X.Y.Z"
   git push origin main
   ```

3. **Create and push a tag**:
   ```bash
   git tag -a v0.1.0 -m "Release version 0.1.0"
   git push origin v0.1.0
   ```

4. **Create a GitHub Release**:
   - Go to the repository's "Releases" page
   - Click "Create a new release"
   - Choose the tag you just created
   - Add release notes
   - Click "Publish release"

The GitHub Action will automatically:
- Build the package
- Authenticate with PyPI using OIDC
- Upload the package to PyPI

## Verifying the Release

After publishing:

```bash
# Install from PyPI
pip install pydantic-typed-cache

# Or from TestPyPI
pip install --index-url https://test.pypi.org/simple/ pydantic-typed-cache
```

## Troubleshooting

### Common Issues

1. **"invalid-pending-publisher" error**:
   - Verify all settings match exactly (owner, repo, workflow, environment)
   - Environment name in workflow must match PyPI settings

2. **First-time publishing**:
   - The package will be created automatically on first successful publish
   - Pending publisher will be converted to active publisher

3. **Permission denied**:
   - Ensure `permissions: id-token: write` is in the workflow
   - Check that the workflow file name matches PyPI settings

## Version Management

Follow semantic versioning:
- `0.1.x` - Initial development, API may change
- `1.0.0` - First stable release
- `1.x.y` - Backward compatible changes
- `2.0.0` - Breaking changes

## Security Notes

- No API tokens are stored in GitHub Secrets
- Authentication happens via OIDC (OpenID Connect)
- Each environment (pypi, testpypi) has separate trusted publisher settings
- Releases require explicit tagging and release creation
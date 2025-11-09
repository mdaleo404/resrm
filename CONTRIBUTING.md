# How to Contribute to `resrm`

Thanks for your interest in contributing to `resrm`! This guide walks you through the process step by step so you can send contributions with confidence.

### For external contributors

1. **Fork the repository** via GitHub: click *Fork* at the top right.
2. **Clone your fork**:

   ```bash
   git clone https://github.com/<your-username>/resrm.git
   cd resrm
   ```
3. **Add the upstream repo** so you can sync later:

   ```bash
   git remote add upstream https://github.com/mdaleo404/resrm.git
   ```
4. **Create a feature branch**:

   ```bash
   git checkout -b feature/my-new-thing
   ```
5. Make your changes and test them locally.
6. **Push to your fork**:

   ```bash
   git push -u origin feature/my-new-thing
   ```
7. Open a **Pull Request** targeting the `main` branch of the upstream repo.

### For maintainers

You may create branches directly in the main repository without forking.

## Commit Message Style Commit Message Style

To keep the automated changelog clean, follow this commit style:

**Format:**

```
type: short description
```

**Accepted types:**

* `feat:` new features
* `fix:` bug fixes
* `refactor:` internal improvements
* `perf:` performance changes
* `docs:` documentation updates
* `chore:` maintenance
* `test:` test-only changes

**Examples:**

```
feat: add --dry-run flag
fix: handle unicode paths
refactor: simplify cleanup logic
```

Don’t overthink it — the maintainer can adjust commit types during merge if needed.

## What Happens After You Submit a PR?

After reviewing your changes, your PR (hopefully) gets merged. Then:

* **Release Please** automatically creates a **release PR** summarizing changes
* The maintainer merges that release PR
* A GitHub Release is created
* The package is published to PyPI
* Wheels, source tarballs, and checksums are attached to the GitHub Release

No need to bump versions manually (unless needed).

## Code Style

* Follow standard Python formatting
* Add type hints when possible
* Keep functions small and readable
* Stick to clear naming

## Need Help, Found a Bug, Have a Request?

If you're unsure about anything:

* **Open an issue**
* Start a discussion
* Ask questions before writing lots of code

## Thank You

Your contributions — large or small — help make `resrm` better for everyone. Thanks for being part of the project!
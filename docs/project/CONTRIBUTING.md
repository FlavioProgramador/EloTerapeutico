# Contributing Guidelines

Thank you for considering contributing to **Elo Terapêutico**! This document outlines how to get started, the workflow we use, and the standards we expect.

## 📚 Getting Started
1. **Fork** the repository.
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/your-username/elo-terapeutico.git
   cd elo-terapeutico
   ```
3. **Create a branch** for your feature or bug‑fix:
   ```bash
   git checkout -b feature/awesome-feature
   ```
4. Follow the **Setup Local** instructions in the README to get the backend and frontend running.

## 🔧 Development Workflow
- **Commit messages** must follow the **Conventional Commits** format:
  - `feat:` a new feature
  - `fix:` a bug fix
  - `docs:` documentation only changes
  - `refactor:` code changes that neither fix a bug nor add a feature
  - `test:` adding or correcting tests
- **Push** your branch and open a **Pull Request** targeting `main`.
- Ensure that **GitHub Actions** pass (unit tests, lint, build).
- Request a review from a maintainer. Once approved, the PR can be merged.

## ✅ Checklist for PRs
- [ ] Tests added/updated (if applicable).
- [ ] Lint passes (flake8/black for Python, ESLint/Prettier for JS/TS).
- [ ] Updated documentation (README, API_SPEC, etc.) if necessary.
- [ ] No secrets or credentials in the diff.
- [ ] Passes CI workflow.

---

*Feel free to open an issue first if you’re unsure about the scope or design of your change.*

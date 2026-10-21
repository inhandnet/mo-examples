# Contributing to mo-examples

Contributions should help people use and develop with Mo series single-board computers. Submit changes through a pull request to `master`.

## Before you start

- Open an issue for bugs and feature requests using the issue forms. Questions about using a product belong in the [community forum](https://community.inhand.com).
- Do not include private infrastructure details, credentials, or confidential material in code, commit messages or pull requests. Follow [SECURITY.md](SECURITY.md) for security-related concerns.
- Only contribute material you have the right to share under the repository [LICENSE](LICENSE). State the license of any third-party content next to it.

## Local setup

Enable the Git hooks once per clone so the commit message check runs locally:

```bash
git config core.hooksPath .githooks
```

The `commit-msg` hook checks each commit message; the `pre-push` hook checks every commit that is about to be pushed. Both call `scripts/check-commit-msg.sh`, which is also what CI runs.

Before opening a pull request, run the same checks as CI where they apply to your change:

```bash
shellcheck $(git ls-files '*.sh')
python3 -m py_compile $(git ls-files '*.py')
yamllint .
```

## Commit message convention

Commit messages and pull request titles use this format:

```text
<type>(<scope>): <subject>
```

- Allowed types: `feat`, `fix`, `docs`, `refactor`, `sync`, `ci`, and `chore`.
- The scope is optional. When present, use lowercase letters, digits, and hyphens; use `/` to separate scope segments.
- Start the subject with a lowercase letter and do not end it with a period.
- Keep the complete title within 72 characters.
- If a body is needed, separate it from the title with a blank line. Wrap body lines at 72 characters; URLs and indented code are exempt.
- Do not include private IP addresses, internal-only domains, or sensitive information.
- End the message with exactly one bilingual block so releases can generate English and Chinese changelogs. Keep the lines within 72 bytes; a Chinese character counts as three bytes.

  ```text
  Message:
    en: Describe the user-visible change in English.
    zh: 用中文描述用户可见的变更。
  ```

Example:

```text
docs(toolchain): describe the host setup steps

Message:
  en: Describe the host setup steps for the toolchain.
  zh: 补充工具链的主机环境配置步骤。
```

The rules are enforced by the [commit-message workflow](.github/workflows/commit-message.yml) using [`scripts/check-commit-msg.sh`](scripts/check-commit-msg.sh). The pull request title, the pull request body and every commit are checked.

## Pull request process

1. Create a branch from `master`; use a short descriptive name such as `feat/benchmark-runner` or `fix/readme-links`.
2. Keep each pull request focused on one change. Squash fix-up commits before pushing.
3. Fill in the pull request template. The title follows the commit message convention, and the body ends with the same `Message` block, because pull requests are squash-merged and the title and body become the commit on `master`.
4. Wait for the `commit-message` and `ci` checks to pass and address review comments.
5. A maintainer squash-merges the pull request. Direct pushes to `master` are not allowed.

## Releases

Maintainers create releases by pushing an annotated tag that matches `V<major>.<minor>.<patch>` or `V<major>.<minor>.<patch>-rc<n>` from a commit on `master`. See the "Releases and tags" section of [README.md](README.md).

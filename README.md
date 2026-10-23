# mo-examples

English | [简体中文](README.zh-CN.md)

Application demos and sample projects for InHand Mo series single-board computers.

This repository will hold runnable demos and sample projects for Mo boards: edge AI applications, camera pipelines, peripheral access, networking, R5F real-time core firmware and ROS 2 integration.

Related repositories:

- [Mo62A](https://github.com/inhandnet/Mo62A) — board support package, OS image build and device-side runtime for the Mo 62A board.
- [mo-docs](https://github.com/inhandnet/mo-docs) — product documentation for the Mo series.

## Status

The directory layout, contribution rules and the CI and release pipelines are in place. `ai/` and `camera/` hold the first batch of examples imported from the Mo62A repository and the mo-docs tutorial packages; `peripherals/`, `network/`, `r5f/` and `ros2/` are still placeholders whose `README.md` describes what will be published there. Importing an example into this repository did not re-build or re-run it; each directory README states what was verified and on which image. Catalog publication does not establish new hardware verification or model hosting.

## Repository layout

| Path | Purpose |
| --- | --- |
| `ai/` | Edge AI examples: C/C++ SDK examples (`edgeai-cpp/`), a Python ONNX Runtime smoke test (`python-smoke/`) and the zone-occupancy tutorial application (`zone-demo/`). |
| `camera/` | Camera examples: IMX219 CSI live preview (`imx219-preview/`). |
| `peripherals/` | Peripheral examples. |
| `network/` | Networking examples. |
| `r5f/` | R5F examples (placeholder, P2). |
| `ros2/` | ROS 2 examples (placeholder, P2). |
| `scripts/` | Repository maintenance scripts (commit message check, changelog generation). |
| `.githooks/` | Git hooks that run the commit message check locally. |
| `.github/` | Issue forms, pull request template and GitHub Actions workflows. |
| `release-notes/` | Changelog baseline used by the release workflow. |

## Contributing

Contributions are welcome through pull requests to `master`. Read [CONTRIBUTING.md](CONTRIBUTING.md) for the commit message convention, the pull request process and how to enable the local Git hooks:

```bash
git config core.hooksPath .githooks
```

Every pull request must pass the `commit-message` and `ci` checks before it can be merged. Use GitHub issues for bugs, reproducible problems and feature requests in this repository.

## Releases and tags

New releases use annotated ordinary `V<major>.<minor>.<patch>` tags on checked `master` commits. Only developer publishes website release candidates. The release workflow validates catalogs, packages source with SPDX SBOM, records the source commit and catalog hashes in `release.json`, writes SHA-256 checksums, then publishes a complete GitHub Release. Historical RCs remain unchanged. Changelog headings are bilingual; entries retain their English commit summaries.

```bash
git switch master
git pull --ff-only
git tag -a V1.0.0 -m "V1.0.0"
git push origin V1.0.0
```

## Security

Do not report security vulnerabilities in public issues. Follow [SECURITY.md](SECURITY.md).

## License

This repository is licensed under the terms in [LICENSE](LICENSE). Third-party content added later keeps its own license, stated next to the content.

## Unified website integration

`examples.json` lists actual source projects, entrypoints, image/model requirements and tutorial routes. Empty scaffold folders are excluded. `source-available` is not a new board-test claim. Developer reads a pinned source revision, validates the combined data, and renders the website; this repository has no documentation-site frontend or website deployment.

Run `node scripts/check-catalog.mjs` and `node --test tests/*.test.mjs` with Node 22. `validation/` is exported from a committed developer contract and checked by hash; do not edit it locally. For integrated preview, run developer's `npm run preview -- --source mo-examples=/path/to/mo-examples`.

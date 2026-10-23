# Contributing to mo-examples

Use a topic branch and a pull request to `master`. Keep changes within this repository's source/data responsibility. Tutorials belong to mo-docs; website rendering and integration belong to developer. The required `ci` and `commit-message` checks must pass before normal protected-branch merging.

## Messages and local checks

Use a short English Conventional Commit, for example `fix: correct the catalog reference`. Follow [repository-policy.json](config/repository-policy.json); no bilingual Message block is required. Do not add Co-Authored-By trailers, private infrastructure details or CI-skip directives. Historical commit summaries remain readable by the changelog generator.

```sh
git config core.hooksPath .githooks
node scripts/check-catalog.mjs
node --test tests/*.test.mjs
```

Use Node 22. CI also checks shell, Python, YAML and JSON files. Run affected business tests with their required environment; static checks do not certify hardware behavior. Preserve source notices, licenses and original validation limits when moving resources. Keep each implementation in one owning repository and consume fixed revisions in other repositories.

## Integration and releases

`validation/` is exported from a committed developer catalog contract. Its lock records file hashes and the exact source commit; update the contract upstream and export it instead of editing the copy. Developer separately validates the actual selected cross-repository combination and website routes.

Create new ordinary annotated `VX.Y.Z` tags only from checked master commits, using the existing authorized release role. Check remote tag availability first. Release CI validates catalogs, packages source and SBOM, records `release.json` and checksums, then publishes the complete release. Only developer uses new RC tags and deploys the website. Never rewrite historical tags or published assets.

PR descriptions should state the changed behavior, validation and remaining limits. No bilingual message template is required. Publish new metadata without converting untested or unavailable resources into supported downloads.

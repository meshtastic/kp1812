<!--
Thank you for contributing to kp1812!
Fill out the sections below. Delete any that don't apply.
-->

## Summary

<!-- One or two sentences: what does this PR do? -->

## Type of change

- [ ] Bug fix (non-breaking)
- [ ] New feature (non-breaking)
- [ ] Breaking change (SemVer-MINOR pre-1.0 / SemVer-MAJOR post-1.0)
- [ ] Documentation only
- [ ] Infrastructure / CI / build

## Related issue / discussion

<!-- Fixes #123 / Refs #456 -->

## Affirmations

- [ ] All commits are signed off (DCO — `git commit -s`).
- [ ] I have read [`CONTRIBUTING.md`](../CONTRIBUTING.md).
- [ ] If this changes the public API, I ran `./gradlew apiDump` **on macOS** and committed both `api/kp1812.api` and `api/kp1812.klib.api`.
- [ ] If this changes what the model computes, `ReferenceConformanceTest` and `EndToEndTest` still pass, and I did **not** hand-edit a generated fixture.
- [ ] If this regenerates the fixtures, it bumps `PY1812_COMMIT` in `scripts/p1812_ref.py` in the same PR and says why.
- [ ] A consumer-visible change has a `CHANGELOG.md` entry under `## [Unreleased]`.

## How was this verified?

<!-- Which targets ran the suite, and on which host. Cross-compiling a target is not testing it. -->

## Notes for reviewers

<!-- Tricky areas, open questions, follow-ups. -->

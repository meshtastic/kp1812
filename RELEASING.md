# Releasing kp1812

kp1812 publishes to Maven Central (`org.meshtastic:kp1812`) via the vanniktech
maven-publish plugin, driven by `.github/workflows/release.yml`.

## One-time setup

The repository needs these GitHub Actions secrets (the vanniktech
`ORG_GRADLE_PROJECT_*` convention):

- `SIGNING_KEY` — the in-memory GPG signing key.
- `OSSRH_USERNAME` / `OSSRH_PASSWORD` — Sonatype Central Portal credentials.
- `DEVELOCITY_ACCESS_KEY` — optional; without it builds publish no scan and
  read the shared cache without writing it.
- `CODECOV_TOKEN` — optional; the coverage status is informational either way.

## Cutting a release

1. Pick the new version `X.Y.Z` (SemVer; pre-1.0 may break in minors).
2. Set `VERSION_NAME` in `gradle.properties` **and** mirror it into `VERSION`.
   The workflow verifies they match and fails otherwise.
3. Run `./gradlew patchChangelog`. It cuts the `## [Unreleased]` entries into a
   dated `## [X.Y.Z]` heading, leaves an empty Unreleased behind, and writes the
   compare links — reading `VERSION_NAME`, so step 2 has to come first. It fails
   if Unreleased is empty (`patchEmpty = false`): a release with nothing to say
   is a release that skipped the changelog. Review the diff; it is what the
   GitHub Release page will say.
4. If the public API changed, regenerate the dump **on macOS** (`./gradlew apiDump`)
   and commit both `api/kp1812.api` and `api/kp1812.klib.api`.
5. Commit (signed off), open the PR, merge it.
6. Trigger the release: push a `vX.Y.Z` tag, or run the **Release** workflow via
   `workflow_dispatch` (it tags for you). Tags in this org are immutable.

## What the workflow does

- Verifies `VERSION`, `VERSION_NAME` and a `## [X.Y.Z]` heading in `CHANGELOG.md`
  agree. `getChangelog` does not fail on a missing section, it prints the
  previous release, so the heading check is what stops that.
- **Waits for the two macOS CI jobs** on the commit being released — the Apple
  test binaries and the full klib ABI check. The publish itself runs on Linux,
  which cross-compiles every target but cannot *execute* the Apple tests; the
  guard is what keeps that guarantee.
- Builds and tests everything a Linux host can run, stages the artifacts,
  attests them, renders the changelog section into the release notes, and only
  then publishes.
- Is **idempotent**: it probes `repo1.maven.org` first and skips the publish if
  `X.Y.Z` is already there, so a re-run after a partial failure is safe.

The first release is where the Linux-publishes-all-targets shape is proven for
this repo; kzstd verified the same shape against its 0.2.0.

## After releasing

Maven Central → repo1 propagation typically takes 10–30 minutes. Verify
`https://repo1.maven.org/maven2/org/meshtastic/kp1812-jvm/X.Y.Z/` resolves
before a consumer bumps.

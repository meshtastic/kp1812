# Releasing kp1812

kp1812 publishes `org.meshtastic:kp1812` to Maven Central with the vanniktech
maven-publish plugin, from `.github/workflows/release.yml`. Each release also
carries a static `Kp1812.xcframework.zip` and the `Package.swift` that names it,
for SwiftPM.

## Secrets

The repository needs these GitHub Actions secrets, passed as the vanniktech
`ORG_GRADLE_PROJECT_*` properties:

| Secret | Holds |
| --- | --- |
| `SIGNING_KEY` | The org's Maven signing key `4C9706AEE7CC2A92`, ASCII-armored |
| `SIGNING_PASSWORD` | That key's passphrase |
| `OSSRH_USERNAME`, `OSSRH_PASSWORD` | Sonatype Central Portal credentials |
| `DEVELOCITY_ACCESS_KEY` | Optional. Without it, builds publish no scan and read the shared cache without writing it |
| `CODECOV_TOKEN` | Optional. The coverage status is informational either way |

Export the key with `gpg --pinentry-mode loopback --armor --export-secret-keys
4C9706AEE7CC2A92`, which asks for the passphrase in the terminal.

## Cutting a release

1. Pick `X.Y.Z` (SemVer; before 1.0 a minor may break).
2. On a branch, set `VERSION` and `VERSION_NAME` in `gradle.properties` to
   `X.Y.Z`, and run `scripts/changelog.sh cut X.Y.Z`. That moves
   `## [Unreleased]` under a dated `## [X.Y.Z]` heading and updates the compare
   links, touching nothing else. It refuses an empty Unreleased.
3. If the public API changed, regenerate the dump **on macOS** (`./gradlew
   apiDump`) and commit both `api/kp1812.api` and `api/kp1812.klib.api`.
4. Commit `chore(release): X.Y.Z` (signed off), open the PR and merge it.
5. `gh workflow run release.yml --repo meshtastic/kp1812 -f version=X.Y.Z`. Add
   `-f dry_run=true` to run every gate and build everything without tagging,
   publishing or uploading; a dry run may start from any branch. Pushing a
   `vX.Y.Z` tag on `main` runs the same workflow.

## What the workflow checks, in order

1. The commit is on `main` (skipped for a dry run).
2. The version equals `VERSION` and `VERSION_NAME`, and any existing `vX.Y.Z`
   tag points at this commit.
3. `scripts/changelog.sh notes X.Y.Z` finds a non-empty section. It becomes the
   GitHub Release body verbatim.
4. The two macOS CI jobs passed on this commit (`scripts/release-checks.sh
   green-ci`): the Apple test binaries and the full klib ABI check. The workflow
   names them, because `main` has no ruleset requiring checks. This Linux runner
   cross-compiles every target but cannot run the Apple tests.
5. `./gradlew build`, then `publishToMavenLocal` with signing.
6. No staged POM or Gradle module depends on a `-SNAPSHOT`
   (`scripts/release-checks.sh no-snapshots`). Central rejects that only after
   upload.
7. If `X.Y.Z` is already on `repo1.maven.org` the publish is skipped, so a
   re-run is safe.

Then it attests every staged artifact, pushes the annotated `vX.Y.Z` tag if it
is missing, runs `publishAndReleaseToMavenCentral`, which releases the
deployment on Central without a manual step in the portal, and creates or
updates the GitHub Release.

## XCFramework and Swift package

A second job, on macOS, checks out the same commit, builds `Kp1812.xcframework`
and zips it with `scripts/swift-package.sh`. It attests the zip and attaches it
to the release with the `Package.swift` that names it by URL and checksum. A
re-run replaces both, so the checksum always matches the zip beside it. A dry
run builds and zips, and attests and uploads nothing.

## After releasing

`repo1.maven.org` lags the Central Portal by 10 to 30 minutes. Downstream bumps
wait until `https://repo1.maven.org/maven2/org/meshtastic/kp1812-jvm/X.Y.Z/`
resolves.

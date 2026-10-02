# Releasing kp1812

kp1812 publishes to Maven Central (`org.meshtastic:kp1812`) through the
vanniktech maven-publish plugin, driven by `.github/workflows/release.yml`.

## One-time setup

The repository needs these GitHub Actions secrets, named for the vanniktech
`ORG_GRADLE_PROJECT_*` convention:

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

1. Pick the new version `X.Y.Z` (SemVer; before 1.0 a minor version can break).
2. Set `VERSION_NAME` in `gradle.properties` **and** mirror it into `VERSION`.
   The workflow fails unless they match.
3. Run `./gradlew patchChangelog`. It reads `VERSION_NAME`, so step 2 comes
   first. It moves the `## [Unreleased]` entries under a dated `## [X.Y.Z]`
   heading, leaves an empty Unreleased behind, and writes the compare links.
4. Review the changelog diff, which becomes the GitHub release page. The task
   fails if Unreleased is empty (`patchEmpty = false`), because a release with
   nothing to say skipped the changelog.
5. If the public API changed, regenerate the dump **on macOS** (`./gradlew
   apiDump`) and commit both `api/kp1812.api` and `api/kp1812.klib.api`.
6. Commit (signed off), open the PR, and merge it.
7. Trigger the release: push a `vX.Y.Z` tag, or run the **Release** workflow
   through `workflow_dispatch`, which tags for you. Tags in this org are
   immutable.

## What the workflow does

- Verifies that `VERSION`, `VERSION_NAME`, and a `## [X.Y.Z]` heading in
  `CHANGELOG.md` agree. `getChangelog` doesn't fail on a missing section. It
  prints the previous release instead, so the heading check is what stops that.
- **Waits for the two macOS CI jobs** on the commit being released: the Apple
  test binaries and the full klib ABI check. The publish runs on Linux, which
  cross-compiles every target but can't execute the Apple tests, so this guard
  keeps that guarantee.
- Builds and tests everything a Linux host can run, stages the artifacts,
  attests them, renders the changelog section into the release notes, and only
  then publishes.
- Is **idempotent**. It probes `repo1.maven.org` first and skips the publish if
  `X.Y.Z` is already there, so a re-run after a partial failure is safe.
- Then, on macOS, builds `Kp1812.xcframework` from the tag and zips it with
  `scripts/swift-package.sh`. It attaches the zip and the `Package.swift` that
  names it (URL and checksum) to the release. A re-run replaces both, so the
  checksum always matches the zip beside it.

## After releasing

Propagation from the Central Portal to repo1 takes 10 to 30 minutes. Before a
consumer bumps, confirm that
`https://repo1.maven.org/maven2/org/meshtastic/kp1812-jvm/X.Y.Z/` resolves.

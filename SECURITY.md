# Security policy

## Reporting a vulnerability

**Do not open a public GitHub issue.** Report it privately instead:

- File a private [GitHub Security Advisory](https://github.com/meshtastic/kp1812/security/advisories/new).
- Email security@meshtastic.org.

Meshtastic aims to acknowledge reports within five business days and to ship a
fix or mitigation within 90 days, depending on severity. The advisory credits
you unless you'd prefer to remain anonymous.

## Supported versions

kp1812 is pre-1.0. Only the latest published release receives security fixes,
and there are no long-term support branches.

## Threat model

kp1812 is a pure numeric library. It takes `DoubleArray`/`IntArray` terrain
profiles and scalar parameters and returns numbers. It parses no binary
formats, reads no files, opens no sockets, and has **zero runtime
dependencies**.

That makes the realistic concerns narrow:

- **Untrusted profile input.** Callers can pass terrain from a remote source.
  The library validates path invariants (ascending distances, matching array
  lengths, and a minimum point count) and parameter ranges up front. It throws
  `IllegalArgumentException` rather than producing a silent nonsense result. A
  malformed profile should never loop forever or allocate without bound, and
  one that does is a bug worth reporting here.
- **Supply chain.** `.github/workflows/release.yml` publishes every artifact
  GPG-signed, with build provenance attested for each one. The `vX.Y.Z` tag it
  pushes is annotated and unsigned. Verify signatures if you consume from Maven
  Central.

A prediction you disagree with isn't a security issue. P.1812 is a statistical
model with substantial inherent uncertainty, and accuracy reports are welcome as
ordinary issues.

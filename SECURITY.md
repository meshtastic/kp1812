# Security policy

## Reporting a vulnerability

**Do not open a public GitHub issue.** Instead:

- File a private [GitHub Security Advisory](https://github.com/meshtastic/kp1812/security/advisories/new), or
- email security@meshtastic.org.

We aim to acknowledge reports within 5 business days and to ship a fix or
mitigation within 90 days, depending on severity. You will be credited in the
advisory unless you prefer to remain anonymous.

## Supported versions

kp1812 is pre-1.0. Only the latest published release receives security fixes;
there are no long-term support branches.

## Threat model

kp1812 is a pure numeric library. It takes `DoubleArray`/`IntArray` terrain
profiles and scalar parameters and returns numbers. It parses no binary
formats, reads no files, opens no sockets, and has **zero runtime
dependencies**.

That makes the realistic concerns narrow:

- **Untrusted profile input.** Callers may pass terrain from a remote source.
  The library validates path invariants (ascending distances, matching array
  lengths, minimum point count) and parameter ranges up front and throws
  `IllegalArgumentException` rather than producing a silent nonsense result.
  A malformed profile should never loop forever or allocate unboundedly —
  if you find one that does, that is a bug worth reporting here.
- **Supply chain.** Releases are published by `.github/workflows/release.yml`
  from a tagged commit, signed, with build provenance attested. Verify
  signatures if you consume from Maven Central.

What is explicitly **not** a security issue: a prediction you disagree with.
P.1812 is a statistical model with substantial inherent uncertainty. Accuracy
reports are welcome as ordinary issues.

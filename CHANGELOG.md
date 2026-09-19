# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project
adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial implementation of Recommendation ITU-R P.1812-8: free-space and
  line-of-sight loss, β₀, effective earth radius, smooth-earth heights and
  horizon geometry, Bullington and delta-Bullington diffraction,
  spherical-earth first-term diffraction, diffraction for p% time,
  troposcatter, ducting / layer reflection, location variability, and their
  combination into basic transmission loss and field strength.
- Public API: `TerrainPath`, `Atmosphere`, `Prediction`, `Polarization`,
  `P1812.predict()` and `P1812.receivedPower()`.
- Conformance suite checking every function against calls captured from the
  ITU reference implementation over its 19 official validation profiles,
  executing on all 13 targets.
- End-to-end conformance: 63 whole-model cases spanning 0.03–6 GHz (the
  Recommendation's full range), time percentages 1/10/20/50, both
  polarizations and profiles of 6–2001 points. Worst deviation in basic
  transmission loss is 3.3e-9 dB.
- The fixture pipeline itself, under `scripts/`: capture from the reference,
  emit the Kotlin, pinned to `eeveetza/Py1812` at `6c9061dd` (P.1812-8), so a
  regeneration says what it was captured from and cannot drift silently.

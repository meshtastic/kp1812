// SPDX-License-Identifier: GPL-3.0-or-later
import org.gradle.api.tasks.bundling.AbstractArchiveTask
import org.jetbrains.kotlin.gradle.ExperimentalWasmDsl
import org.jetbrains.kotlin.gradle.plugin.mpp.apple.XCFramework

plugins {
    alias(libs.plugins.kotlin.multiplatform)
    alias(libs.plugins.vanniktech.publish)
    alias(libs.plugins.dokka)
    alias(libs.plugins.binary.compat)
    alias(libs.plugins.kover)
    alias(libs.plugins.spotless)
    alias(libs.plugins.detekt)
}

// GROUP and VERSION_NAME come from gradle.properties, the single coordinate source the
// vanniktech plugin reads; they're mirrored onto the project for non-publish tasks.
group = providers.gradleProperty("GROUP").getOrElse("org.meshtastic")
version = providers.gradleProperty("VERSION_NAME").getOrElse("0.1.0")

repositories {
    mavenCentral()
}

kotlin {
    // The toolchain fixes the bytecode at 21 but not the API: built on a newer JDK, a call to
    // a 22+ method compiles, publishes, and fails on a consumer's 21 at runtime. -Xjdk-release
    // limits the JDK classpath too; the three numbers move together.
    jvmToolchain(21)
    explicitApi()

    compilerOptions {
        // Warnings are errors on every target, main and test. The model is pure
        // arithmetic over the stdlib, so there is nothing here that needs an exemption.
        allWarningsAsErrors.set(true)
        progressiveMode.set(true)
    }

    jvm {
        compilerOptions { freeCompilerArgs.add("-Xjdk-release=21") }
    }

    // P.1812 is pure kotlin.math in commonMain on every target: no expect/actual,
    // no cinterop, and no platform-specific code. IR is the only Kotlin/JS compiler in
    // 2.4+, so a plain `js {}` selects it.
    js {
        browser()
        nodejs()
    }

    @OptIn(ExperimentalWasmDsl::class)
    wasmJs {
        browser()
        nodejs()
    }

    @OptIn(ExperimentalWasmDsl::class)
    wasmWasi {
        nodejs()
    }

    // The nine native targets compile the same commonMain source as everything else.
    // Deliberately no androidTarget: Android consumes the jvm() artifact, which keeps
    // AGP and the Android SDK out of the build entirely (same choice as kzstd).
    // Swift consumes the Apple targets as one static XCFramework, which SwiftPM takes as a
    // binaryTarget; scripts/swift-package.sh zips it and writes the manifest. Kotlin/Native
    // has no Mac Catalyst target, so a Catalyst build cannot link it.
    val xcf = XCFramework("Kp1812")
    listOf(
        iosArm64(),
        iosSimulatorArm64(),
        iosX64(),
        macosArm64(),
        tvosArm64(),
        tvosSimulatorArm64(),
    ).forEach { target ->
        target.binaries.framework {
            baseName = "Kp1812"
            binaryOption("bundleId", "org.meshtastic.kp1812")
            isStatic = true
            xcf.add(this)
        }
    }
    linuxX64()
    linuxArm64()
    mingwX64()

    applyDefaultHierarchyTemplate()

    sourceSets {
        // kp1812 has ZERO runtime dependencies: the model uses only the Kotlin stdlib.
        commonTest.dependencies {
            implementation(kotlin("test"))
        }
    }
}

// Validate the full cross-platform ABI (klib/native + common), not JVM only. A JVM-only
// dump lets the klib surface change underneath it (AGENTS.md, Design invariants).
apiValidation {
    @OptIn(kotlinx.validation.ExperimentalBCVApi::class)
    klib {
        enabled = true
    }
}

tasks.withType<JavaCompile>().configureEach { options.release.set(21) }

// Reproducible archives: stable file order + zeroed timestamps so published artifacts
// are byte-deterministic across builds.
tasks.withType<AbstractArchiveTask>().configureEach {
    isReproducibleFileOrder = true
    isPreserveFileTimestamps = false
}

// ─────────────────────────────────────────────────────────────────────────────
// Code quality: Spotless (ktlint formatting) + detekt (static analysis). ktlint honors
// the repo .editorconfig, so the two share one style source of truth.
spotless {
    kotlin {
        target("src/**/*.kt")
        ktlint(libs.versions.ktlint.get())
        // A new file is stamped by `spotlessApply`, not by someone remembering. The generated
        // fixtures are excluded: their header is the generator's, and carries the reference pin.
        targetExclude(
            "src/commonTest/kotlin/org/meshtastic/kp1812/ReferenceFixtures.kt",
            "src/commonTest/kotlin/org/meshtastic/kp1812/E2EFixtures.kt",
        )
        licenseHeaderFile(rootProject.file("config/spotless/license-header.txt"))
    }
    kotlinGradle {
        target("*.gradle.kts")
        ktlint(libs.versions.ktlint.get())
    }
}

detekt {
    buildUponDefaultConfig = true
    allRules = false
    config.setFrom(files("$rootDir/config/detekt/detekt.yml"))
    basePath = rootDir.absolutePath
    // A multiplatform project has no `main`/`test` Java source sets, so the default
    // detekt task finds NO-SOURCE and reports green over an unchecked tree. Point it
    // at the Kotlin source sets explicitly.
    source.setFrom(
        kotlin.sourceSets.flatMap { it.kotlin.srcDirs }.filter { it.exists() },
    )
}

tasks.withType<io.gitlab.arturbosch.detekt.Detekt>().configureEach {
    reports {
        html.required.set(true)
        sarif.required.set(true)
        md.required.set(false)
        txt.required.set(false)
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Publishing. Dokka feeds the javadoc jar: Maven Central accepts a 261-byte empty stub
// without complaint, which is how repos end up published with no API docs at all.
mavenPublishing {
    publishToMavenCentral()
    // Sign only when a key is actually configured. Central requires signatures, and CI supplies
    // them; requiring them unconditionally means `publishToMavenLocal` fails for anyone without
    // a GPG key, which is every contributor trying the library against their own app.
    if (providers.gradleProperty("signingInMemoryKey").isPresent ||
        providers.gradleProperty("signing.keyId").isPresent
    ) {
        signAllPublications()
    }

    pom {
        name.set("kp1812")
        description.set(
            "Recommendation ITU-R P.1812 terrestrial point-to-area propagation prediction, " +
                "in pure Kotlin Multiplatform.",
        )
        inceptionYear.set("2026")
        url.set("https://github.com/meshtastic/kp1812")
        licenses {
            license {
                name.set("GNU General Public License v3.0 or later")
                url.set("https://www.gnu.org/licenses/gpl-3.0.txt")
                distribution.set("repo")
            }
        }
        developers {
            developer {
                id.set("meshtastic")
                name.set("Meshtastic")
                url.set("https://github.com/meshtastic")
            }
        }
        scm {
            url.set("https://github.com/meshtastic/kp1812")
            connection.set("scm:git:git://github.com/meshtastic/kp1812.git")
            developerConnection.set("scm:git:ssh://git@github.com/meshtastic/kp1812.git")
        }
    }
}

// Security floors for the Kotlin/JS test harness (karma/webpack/mocha stack in
// kotlin-js-store/yarn.lock). They're dev-time only, and nothing here ships in published
// artifacts. Each pin clears an open Dependabot alert; drop a resolution once
// the transitive tree requires at least that version on its own.
// After changing these, regenerate the lock: ./gradlew kotlinUpgradeYarnLock
plugins.withType<org.jetbrains.kotlin.gradle.targets.js.yarn.YarnPlugin> {
    the<org.jetbrains.kotlin.gradle.targets.js.yarn.YarnRootExtension>().apply {
        resolution("ws", "8.21.0") // GHSA memory-exhaustion DoS (< 8.21.0)
        resolution("serialize-javascript", "7.0.5") // RCE (< 7.0.3) + CPU-exhaustion DoS (< 7.0.5)
        resolution("webpack", "5.104.1") // buildHttp allow-list bypasses (< 5.104.1)
        resolution("diff", "8.0.3") // parsePatch/applyPatch DoS (< 8.0.3)
        resolution("brace-expansion", "2.1.7") // Dependabot HIGH ReDoS + OOM DoS (< 2.1.7)
        resolution("fast-uri", "3.1.8") // Dependabot HIGH host confusion (< 3.1.8)
        resolution("js-yaml", "4.3.2") // Dependabot HIGH quadratic CPU in !!omap (< 4.3.2)
        resolution("qs", "6.16.0") // Dependabot MEDIUM (< 6.16.0)
        resolution("body-parser", "1.20.6") // Dependabot LOW (< 1.20.6)
        resolution("socket.io-parser", "4.2.7") // Dependabot HIGH memory-exhaustion DoS (< 4.2.7)
    }
}

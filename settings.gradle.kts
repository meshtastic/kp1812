// SPDX-License-Identifier: GPL-3.0-or-later
pluginManagement {
    repositories {
        gradlePluginPortal()
        mavenCentral()
    }
}

plugins {
    id("com.gradle.develocity") version "4.5.1"
    id("com.gradle.common-custom-user-data-gradle-plugin") version "2.8.0"
    // A contributor without a JDK 21 gets one downloaded rather than a failure: the daemon
    // pin in gradle/gradle-daemon-jvm.properties names the version, this resolves it.
    id("org.gradle.toolchains.foojay-resolver-convention") version "1.0.0"
}

apply(from = "gradle/develocity.settings.gradle")

rootProject.name = "kp1812"

plugins {
    kotlin("plugin.serialization")
    kotlin("plugin.allopen")
    kotlin("plugin.noarg")
}

@Suppress("UNCHECKED_CAST")
val versions = rootProject.extra["versions"] as Map<String, String>

// lesson kt-06: classes marked with these annotations become open / get a no-arg constructor
allOpen { annotation("workbench.kotlin.OpenForProxies") }
noArg { annotation("workbench.kotlin.NoArgEntity") }

dependencies {
    implementation("org.jetbrains.kotlinx:kotlinx-serialization-json:${versions["serialization"]}")
}

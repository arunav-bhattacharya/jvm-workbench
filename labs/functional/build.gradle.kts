@Suppress("UNCHECKED_CAST")
val versions = rootProject.extra["versions"] as Map<String, String>

// Functional programming in Kotlin. Plain Kotlin for most lessons; fp-07 uses Arrow's Either and Raise,
// and fp-08 uses kotlinx.collections.immutable. Versions match the ones the research notes ran.
dependencies {
    implementation("io.arrow-kt:arrow-core:2.3.0")
    implementation("org.jetbrains.kotlinx:kotlinx-collections-immutable:0.5.2")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:${versions["coroutines"]}")
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:${versions["coroutines"]}")
    "demoImplementation"("org.jetbrains.kotlinx:kotlinx-coroutines-test:${versions["coroutines"]}")
}

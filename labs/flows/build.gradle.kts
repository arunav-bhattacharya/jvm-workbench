@Suppress("UNCHECKED_CAST")
val versions = rootProject.extra["versions"] as Map<String, String>

// Kotlin Flow in depth. Labs are Kotlin. Lesson 8 bridges Flow to Reactor and Reactive Streams,
// so the reactive and reactor modules are here too. Virtual time comes from kotlinx-coroutines-test.
dependencies {
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:${versions["coroutines"]}")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-reactive:${versions["coroutines"]}")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-reactor:${versions["coroutines"]}")
    implementation("io.projectreactor:reactor-core:${versions["reactor"]}")
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:${versions["coroutines"]}")
    testImplementation("io.projectreactor:reactor-test:${versions["reactor"]}")
    // the virtual-time Try-it demos (runTest outside JUnit) need the test library too
    "demoImplementation"("org.jetbrains.kotlinx:kotlinx-coroutines-test:${versions["coroutines"]}")
}

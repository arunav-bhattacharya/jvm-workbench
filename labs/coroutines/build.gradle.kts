@Suppress("UNCHECKED_CAST")
val versions = rootProject.extra["versions"] as Map<String, String>

dependencies {
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:${versions["coroutines"]}")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-reactor:${versions["coroutines"]}")
    implementation("io.projectreactor:reactor-core:${versions["reactor"]}")
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:${versions["coroutines"]}")
    testImplementation("io.projectreactor:reactor-test:${versions["reactor"]}")
    // the virtual-time Try-it demos (runTest outside JUnit) need the test library too; no new artifact
    "demoImplementation"("org.jetbrains.kotlinx:kotlinx-coroutines-test:${versions["coroutines"]}")
}

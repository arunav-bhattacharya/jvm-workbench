@Suppress("UNCHECKED_CAST")
val versions = rootProject.extra["versions"] as Map<String, String>

dependencies {
    implementation("io.projectreactor:reactor-core:${versions["reactor"]}")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:${versions["coroutines"]}")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-reactor:${versions["coroutines"]}")
    testImplementation("io.projectreactor:reactor-test:${versions["reactor"]}")
}

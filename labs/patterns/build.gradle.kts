@Suppress("UNCHECKED_CAST")
val versions = rootProject.extra["versions"] as Map<String, String>

dependencies {
    // used by the Observer lesson to compare a hand-rolled observer with Flow
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:${versions["coroutines"]}")
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:${versions["coroutines"]}")
}

@Suppress("UNCHECKED_CAST")
val versions = rootProject.extra["versions"] as Map<String, String>

dependencies {
    implementation("io.netty:netty-all:${versions["netty"]}")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-core:${versions["coroutines"]}")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-reactor:${versions["coroutines"]}")
    implementation("io.projectreactor:reactor-core:${versions["reactor"]}")
    testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:${versions["coroutines"]}")
    testImplementation("io.projectreactor:reactor-test:${versions["reactor"]}")
    "demoImplementation"("org.jetbrains.kotlinx:kotlinx-coroutines-test:${versions["coroutines"]}")
    runtimeOnly("org.slf4j:slf4j-simple:${versions["slf4j"]}")
}

@Suppress("UNCHECKED_CAST")
val versions = rootProject.extra["versions"] as Map<String, String>

dependencies {
    implementation("net.bytebuddy:byte-buddy:${versions["bytebuddy"]}")
    // JMH benchmarks live in the demo source set only; the annotation processor generates the harness
    "demoImplementation"("org.openjdk.jmh:jmh-core:${versions["jmh"]}")
    "demoAnnotationProcessor"("org.openjdk.jmh:jmh-generator-annprocess:${versions["jmh"]}")
    "demoImplementation"("org.openjdk.jol:jol-core:${versions["jol"]}")
}

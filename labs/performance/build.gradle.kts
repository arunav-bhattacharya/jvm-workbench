@Suppress("UNCHECKED_CAST")
val versions = rootProject.extra["versions"] as Map<String, String>

dependencies {
    // JMH benchmarks are written in Java; the annotation processor generates the harness
    implementation("org.openjdk.jmh:jmh-core:${versions["jmh"]}")
    "annotationProcessor"("org.openjdk.jmh:jmh-generator-annprocess:${versions["jmh"]}")
    "demoAnnotationProcessor"("org.openjdk.jmh:jmh-generator-annprocess:${versions["jmh"]}")
    "solutionAnnotationProcessor"("org.openjdk.jmh:jmh-generator-annprocess:${versions["jmh"]}")
    // JOL reads real field offsets for lesson 4 (false sharing): used by its tests and demos
    "testImplementation"("org.openjdk.jol:jol-core:${versions["jol"]}")
    "demoImplementation"("org.openjdk.jol:jol-core:${versions["jol"]}")
}

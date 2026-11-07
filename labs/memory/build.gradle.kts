@Suppress("UNCHECKED_CAST")
val versions = rootProject.extra["versions"] as Map<String, String>

dependencies {
    // JOL prints real object layouts and sizes
    implementation("org.openjdk.jol:jol-core:${versions["jol"]}")
}

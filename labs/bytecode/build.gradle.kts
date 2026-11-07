@Suppress("UNCHECKED_CAST")
val versions = rootProject.extra["versions"] as Map<String, String>

dependencies {
    implementation("net.bytebuddy:byte-buddy:${versions["bytebuddy"]}")
    implementation("net.bytebuddy:byte-buddy-agent:${versions["bytebuddy"]}")
}

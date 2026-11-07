@Suppress("UNCHECKED_CAST")
val versions = rootProject.extra["versions"] as Map<String, String>

dependencies {
    implementation("io.netty:netty-all:${versions["netty"]}")
    implementation("io.vertx:vertx-core:${versions["vertx"]}")
}

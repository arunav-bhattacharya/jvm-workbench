@Suppress("UNCHECKED_CAST")
val versions = rootProject.extra["versions"] as Map<String, String>

dependencies {
    implementation("io.netty:netty-all:${versions["netty"]}")
    implementation("io.vertx:vertx-core:${versions["vertx"]}")
    implementation("io.vertx:vertx-web:${versions["vertx"]}")
    implementation("org.eclipse.jetty:jetty-server:${versions["jetty"]}")
    testImplementation("io.vertx:vertx-junit5:${versions["vertx"]}")
}

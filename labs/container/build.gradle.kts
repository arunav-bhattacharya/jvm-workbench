plugins {
    kotlin("plugin.allopen")
}

@Suppress("UNCHECKED_CAST")
val versions = rootProject.extra["versions"] as Map<String, String>

// cap4-02: Kotlin classes marked @OpenForProxies are compiled open, the way kotlin-spring opens @Component classes
allOpen { annotation("workbench.container.l02.demo.OpenForProxies") }

val sourceSets = extensions.getByType<SourceSetContainer>()

dependencies {
    implementation("net.bytebuddy:byte-buddy:${versions["bytebuddy"]}")
    // the demos run the reference container in src/solution, so they work before you finish a lab
    "demoImplementation"(sourceSets["solution"].output)
    // JMH benchmarks live in the demo source set only; the annotation processor generates the harness
    "demoImplementation"("org.openjdk.jmh:jmh-core:${versions["jmh"]}")
    "demoAnnotationProcessor"("org.openjdk.jmh:jmh-generator-annprocess:${versions["jmh"]}")
    "demoImplementation"("org.openjdk.jol:jol-core:${versions["jol"]}")
}

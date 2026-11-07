package workbench.startup.l03.demo

import java.time.Instant
import java.util.Random

/**
 * Static state computed in a class initializer. On the JVM it is computed again on every start.
 * In a native image built with build-time initialization (the Quarkus default), the initializer
 * runs once, inside the build, and every start of the binary sees the build's values.
 */
object InstanceInfo {
    val startedAt: Instant = Instant.now()                // build-time init: the build's time, forever
    val jitter = Random()                                 // build-time init: the native builder rejects it
}

fun main() {
    println("started at: ${InstanceInfo.startedAt}")
    println("retry jitter ms: ${InstanceInfo.jitter.nextInt(250)}")
}

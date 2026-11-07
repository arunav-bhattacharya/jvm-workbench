package workbench.memory.l03

import workbench.memory.Jvm
import java.util.concurrent.atomic.AtomicInteger

private val finalizedCount = AtomicInteger()

class KLegacyHandle {
    // Kotlin has no override for finalize(): you declare it, and the JVM calls it
    protected fun finalize() {
        finalizedCount.incrementAndGet()
    }
}

/** 1,000 objects with a finalize() method, in two child JVMs: default, and --finalization=disabled. */
fun main(args: Array<String>) {
    if (args.isEmpty()) {
        println("== default flags")
        Jvm.run(listOf(), "workbench.memory.l03.FinalizerDemoKt", "run")
        println("== --finalization=disabled")
        Jvm.run(listOf("--finalization=disabled"), "workbench.memory.l03.FinalizerDemoKt", "run")
        return
    }
    repeat(1_000) { KLegacyHandle() }
    repeat(20) { System.gc(); Thread.sleep(20) }
    println("finalized ${finalizedCount.get()} of 1000")
}

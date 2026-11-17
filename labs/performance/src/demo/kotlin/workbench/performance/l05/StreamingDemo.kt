package workbench.performance.l05

import jdk.jfr.consumer.RecordingStream
import java.time.Duration

// Kotlin twin of StreamingDemo.java: slow store calls and garbage collections, live, from inside the JVM.
fun main() {
    RecordingStream().use { rs ->
        rs.enable("workbench.StoreCall").withThreshold(Duration.ofMillis(35))   // only the slow ones
        rs.enable("jdk.GarbageCollection")
        rs.onEvent("workbench.StoreCall") { e ->
            println("slow store call: ${e.getString("shelf")}, ${e.duration.toMillis()} ms")
        }
        rs.onEvent("jdk.GarbageCollection") { e ->
            println("GC: %s, %.1f ms pause total".format(e.getString("name"), e.getDuration("sumOfPauses").toNanos() / 1e6))
        }
        rs.startAsync()                     // events arrive on a background thread
        kRunWorkload(3)
        Thread.sleep(1_500)                 // let the last flush reach us
    }
}

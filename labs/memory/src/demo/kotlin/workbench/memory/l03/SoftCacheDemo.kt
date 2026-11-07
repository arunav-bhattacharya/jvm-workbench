package workbench.memory.l03

import workbench.memory.Jvm
import java.lang.ref.SoftReference

/** A 40 MB soft-referenced "rate table" in a 64 MB heap, then another 40 MB allocation. Runs in a child JVM. */
fun main(args: Array<String>) {
    if (args.isEmpty()) {
        Jvm.run(listOf("-Xmx64m", "-Xlog:gc"), "workbench.memory.l03.SoftCacheDemoKt", "run")
        return
    }
    val rates = SoftReference(ByteArray(40 shl 20))
    println("rate table cached: ${rates.get() != null}")
    val report = ByteArray(40 shl 20)                     // only fits if the GC clears the soft reference
    println("after a 40 MB report: rate table cached: ${rates.get() != null}, report ${report.size} bytes")
}

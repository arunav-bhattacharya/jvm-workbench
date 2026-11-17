package workbench.memory.l03

import workbench.memory.Jvm
import java.lang.ref.SoftReference

/** A 40 MB decoded photo behind a soft reference in a 64 MB heap, then another 40 MB allocation. Runs in a child JVM. */
fun main(args: Array<String>) {
    if (args.isEmpty()) {
        Jvm.run(listOf("-Xmx64m", "-Xlog:gc"), "workbench.memory.l03.SoftCacheDemoKt", "run")
        return
    }
    val beach = SoftReference(ByteArray(40 shl 20))       // a decoded photo, kept "if there's room"
    println("beach photo cached: ${beach.get() != null}")
    val dog = ByteArray(40 shl 20)                        // only fits if the GC clears the soft reference
    println("after decoding a 40 MB dog photo: beach photo cached: ${beach.get() != null}, dog ${dog.size} bytes")
}

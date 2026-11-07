package workbench.memory.l03

import java.lang.ref.PhantomReference
import java.lang.ref.Reference
import java.lang.ref.ReferenceQueue
import java.lang.ref.SoftReference
import java.lang.ref.WeakReference

/** One object on each rung of the reachability ladder, before and after a GC. */
fun main() {
    val queue = ReferenceQueue<ByteArray>()
    val strong = ByteArray(1_000)                                         // a plain local: strongly reachable
    val soft = SoftReference(ByteArray(1_000), queue)
    val weak = WeakReference(ByteArray(1_000), queue)
    val phantom = PhantomReference(ByteArray(1_000), queue)

    println("before GC: soft ${soft.get() != null}, weak ${weak.get() != null}, phantom.get() ${phantom.get()}")
    System.gc()                                                           // a request; fine in a demo, never a guarantee
    println("after GC:  soft ${soft.get() != null}, weak ${weak.get() != null}, phantom.get() ${phantom.get()}")
    while (true) {
        val r = queue.remove(500) ?: break
        println("enqueued: ${r.javaClass.simpleName}")
    }
    Reference.reachabilityFence(strong)                                   // keep `strong` alive until here
    println("strong array still here: ${strong.size} bytes")
}

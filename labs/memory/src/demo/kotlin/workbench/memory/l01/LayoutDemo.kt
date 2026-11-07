package workbench.memory.l01

import com.sun.management.ThreadMXBean
import org.openjdk.jol.datamodel.Model64_Lilliput
import org.openjdk.jol.info.ClassLayout
import org.openjdk.jol.info.GraphLayout
import org.openjdk.jol.layouters.HotSpotLayouter
import workbench.memory.Jvm
import java.lang.management.ManagementFactory

/** The same fields as the Java demo's Payment. Kotlin properties compile to the same JVM fields. */
class KPayment {
    var captured = false
    var amountMinor = 0L
    var status: Byte = 0
    var currency: String? = null
    var attempts = 0
    var metadata: Any? = null
}

/**
 * Prints real object layouts with JOL. Pass JVM flags to see them change, for example
 * -Pargs=-XX:-UseCompressedOops (the demo then reruns itself in a child JVM with those flags).
 */
fun main(args: Array<String>) {
    if (args.isNotEmpty()) {                                    // flags given: rerun in a JVM that has them
        Jvm.run(args.toList(), "workbench.memory.l01.LayoutDemoKt")
        return
    }
    println(ClassLayout.parseClass(KPayment::class.java).toPrintable())

    val boxed = ArrayList<Int>()                                // List<Int> holds boxed Integers
    for (i in 0 until 1_000) boxed.add(i)
    println("Object %d, Integer %d, Long %d, String shell %d bytes".format(
        ClassLayout.parseClass(Any::class.java).instanceSize(), ClassLayout.parseClass(Int::class.javaObjectType).instanceSize(),
        ClassLayout.parseClass(Long::class.javaObjectType).instanceSize(), ClassLayout.parseClass(String::class.java).instanceSize()))
    println("\"EUR\" with its byte[]: %d bytes".format(GraphLayout.parseInstance(String("EUR".toCharArray())).totalSize()))
    println("ArrayList<Integer> of 0..999: %,d bytes, int[1000]: %,d bytes".format(
        GraphLayout.parseInstance(boxed).totalSize(), GraphLayout.parseInstance(IntArray(1_000)).totalSize()))

    // JOL can also simulate a layout: here, an 8-byte compact header with compressed references
    val compact = ClassLayout.parseClass(KPayment::class.java, HotSpotLayouter(Model64_Lilliput(true, 8, false), 25))
    println("Payment with compact headers (JOL simulation): %d bytes".format(compact.instanceSize()))

    // and the JVM itself can tell you: count the bytes 10,000 new Payment objects take
    val threads = ManagementFactory.getThreadMXBean() as ThreadMXBean
    val keep = arrayOfNulls<KPayment>(10_000)                   // allocate the array before we start counting
    val before = threads.currentThreadAllocatedBytes
    for (i in keep.indices) keep[i] = KPayment()
    val bytes = threads.currentThreadAllocatedBytes - before
    println("10,000 Payments allocated %,d bytes: %d per object in this JVM".format(bytes, bytes / keep.size))
}

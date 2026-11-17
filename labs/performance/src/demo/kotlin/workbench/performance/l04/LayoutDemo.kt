package workbench.performance.l04

import org.openjdk.jol.info.ClassLayout

// Kotlin twin of LayoutDemo.java: the same layouts, declared in Kotlin.
// @Volatile var compiles to a volatile field, so JOL sees the same thing as in Java.

class KAdjacent {
    @Volatile var parsed = 0L
    @Volatile var written = 0L
}

open class KParsedField { @Volatile var parsed = 0L }   // superclass fields are laid out first
open class KPad1 : KParsedField() { var p1 = 0L; var p2 = 0L; var p3 = 0L; var p4 = 0L; var p5 = 0L; var p6 = 0L; var p7 = 0L; var p8 = 0L }
open class KWrittenField : KPad1() { @Volatile var written = 0L }
class KPadded : KWrittenField() { var q1 = 0L; var q2 = 0L; var q3 = 0L; var q4 = 0L; var q5 = 0L; var q6 = 0L; var q7 = 0L; var q8 = 0L }

fun main() {
    printLayout(KAdjacent::class.java)
    printLayout(KPadded::class.java)
    // the cell behind LongAdder: the JDK pads it with @Contended
    printLayout(Class.forName("java.util.concurrent.atomic.Striped64\$Cell"))
}

fun printLayout(type: Class<*>) {
    val layout = ClassLayout.parseClass(type)
    println("${type.simpleName}: ${layout.instanceSize()} bytes")
    layout.fields()
        .filter { it.name() in setOf("parsed", "written", "value") }
        .forEach { println("  %-7s at offset %3d".format(it.name(), it.offset())) }
}

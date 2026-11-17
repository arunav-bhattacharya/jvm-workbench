package workbench.kotlin.l03.demo

var lookups = 0

class PaperSpec {
    /** Default mode: SYNCHRONIZED. The first reader runs the initializer under a lock. */
    val sheetGrams: Double by lazy {
        lookups++
        if (lookups == 1) throw IllegalStateException("paper catalogue timed out")
        4.99                                   // one A4 sheet of 80 g/m2 paper
    }
}

fun main() {
    for (mode in LazyThreadSafetyMode.entries) {
        println("$mode -> ${lazy(mode) { 0 }.javaClass.name}")
    }

    val spec = PaperSpec()
    try {
        spec.sheetGrams
    } catch (e: IllegalStateException) {
        println("first read failed: ${e.message}")
    }
    println("second read: ${spec.sheetGrams} (initializer ran $lookups times)")
    println("third read:  ${spec.sheetGrams} (initializer ran $lookups times)")
    println("field: ${PaperSpec::class.java.declaredFields.joinToString { "${it.type.name} ${it.name}" }}")
}

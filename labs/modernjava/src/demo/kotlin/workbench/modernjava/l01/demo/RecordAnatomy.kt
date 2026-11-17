package workbench.modernjava.l01.demo

// a plain data class: Kotlin generates equals, hashCode, toString, componentN and copy
data class Shelfmark(val section: String, val shelf: Int)

// the same data class, also emitted as a real JVM record (java.lang.Record subclass)
@JvmRecord
data class ShelfmarkRecord(val section: String, val shelf: Int)

/** What kotlinc gives a one-line data class, seen from the outside. */
fun main() {
    val a = Shelfmark("FIC", 12)
    val b = Shelfmark("FIC", 12)

    println("toString:   $a")
    println("properties: section=${a.section} shelf=${a.shelf}")
    println("equals:     ${a == b}, same hashCode: ${a.hashCode() == b.hashCode()}")
    println("===:        ${a === b}   (two objects, each with its own identity)")
    println("isRecord:   ${Shelfmark::class.java.isRecord} for the data class, ${ShelfmarkRecord::class.java.isRecord} with @JvmRecord")
    println("components: ${ShelfmarkRecord::class.java.recordComponents.contentToString()}")
    println("superclass: ${ShelfmarkRecord::class.java.superclass.name}")
    println("copy:       ${a.copy(shelf = 13)}")

    synchronized(a) {   // compiles and runs: a data class instance is an ordinary identity object
        println("locked on a data class")
    }
}

package workbench.modernjava.l01.demo

// a plain data class: Kotlin generates equals, hashCode, toString, componentN and copy
data class Point(val x: Int, val y: Int)

// the same data class, also emitted as a real JVM record (java.lang.Record subclass)
@JvmRecord
data class RecordPoint(val x: Int, val y: Int)

/** What kotlinc gives a one-line data class, seen from the outside. */
fun main() {
    val a = Point(3, 4)
    val b = Point(3, 4)

    println("toString:   $a")
    println("properties: x=${a.x} y=${a.y}")
    println("equals:     ${a == b}, same hashCode: ${a.hashCode() == b.hashCode()}")
    println("===:        ${a === b}   (two objects, each with its own identity)")
    println("isRecord:   ${Point::class.java.isRecord} for the data class, ${RecordPoint::class.java.isRecord} with @JvmRecord")
    println("components: ${RecordPoint::class.java.recordComponents.contentToString()}")
    println("superclass: ${RecordPoint::class.java.superclass.name}")
    println("copy:       ${a.copy(y = 10)}")

    synchronized(a) {   // compiles and runs: a data class instance is an ordinary identity object
        println("locked on a data class")
    }
}

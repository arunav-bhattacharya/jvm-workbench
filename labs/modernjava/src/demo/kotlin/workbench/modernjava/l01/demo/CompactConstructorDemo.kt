package workbench.modernjava.l01.demo

import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream
import java.io.InvalidObjectException
import java.io.ObjectInputStream
import java.io.ObjectOutputStream
import java.io.Serializable

// Kotlin's init block is the compact constructor's twin: it runs on every construction.
// Kotlin can't reassign a constructor parameter, so normalizing happens in a factory instead.
data class SpineLabel(val section: String, val shelf: Int) {
    init {
        require(shelf >= 1) { "shelf must be 1 or more: $shelf" }
        require(section == section.uppercase()) { "section must be upper case: $section" }
    }

    constructor(section: String) : this(section, 1)                   // secondary: must delegate

    companion object {
        fun of(section: String, shelf: Int) = SpineLabel(section.uppercase(), shelf)   // normalize, then construct
        fun parse(label: String): SpineLabel {
            val (section, shelf) = label.trim().split(" ")
            return of(section, shelf.toInt())
        }
    }
}

data class PageRangeK(val first: Int, val last: Int) : Serializable {
    init { require(first <= last) { "first > last: $first > $last" } }
}

@JvmRecord                                                            // a real JVM record
data class PageRangeR(val first: Int, val last: Int) : Serializable {
    init { require(first <= last) { "first > last: $first > $last" } }
}

/** Every way of making a data class runs init... except Java deserialization of a plain data class. */
fun main() {
    println(SpineLabel.of("fic", 12))
    println(SpineLabel("BIO"))
    println(SpineLabel.parse("ref 7"))
    try { SpineLabel("FIC", 0) } catch (e: IllegalArgumentException) { println("IAE: ${e.message}") }

    for (range in listOf<Any>(PageRangeK(1, 5), PageRangeR(1, 5))) {
        val bytes = serialize(range)
        swapLastTwoInts(bytes)
        try {
            val back = ObjectInputStream(ByteArrayInputStream(bytes)).use { it.readObject() }
            println("tampered stream gave: $back")
        } catch (e: InvalidObjectException) {
            println("tampered stream rejected: ${e.message}")
        }
    }
}

private fun serialize(o: Any): ByteArray {
    val buf = ByteArrayOutputStream()
    ObjectOutputStream(buf).use { it.writeObject(o) }
    return buf.toByteArray()
}

// the stream ends with the two int fields; swapping them turns (1, 5) into (5, 1)
private fun swapLastTwoInts(b: ByteArray) {
    val n = b.size
    for (i in 0 until 4) {
        val t = b[n - 8 + i]
        b[n - 8 + i] = b[n - 4 + i]
        b[n - 4 + i] = t
    }
}

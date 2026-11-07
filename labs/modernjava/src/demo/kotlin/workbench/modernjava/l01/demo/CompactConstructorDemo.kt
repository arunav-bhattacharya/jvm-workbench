package workbench.modernjava.l01.demo

import java.io.ByteArrayInputStream
import java.io.ByteArrayOutputStream
import java.io.InvalidObjectException
import java.io.ObjectInputStream
import java.io.ObjectOutputStream
import java.io.Serializable

// Kotlin's init block is the compact constructor's twin: it runs on every construction.
// Kotlin can't reassign a constructor parameter, so normalizing happens in a factory instead.
data class Amount(val minor: Long, val currency: String) {
    init {
        require(minor >= 0) { "negative amount: $minor" }
        require(currency == currency.uppercase()) { "currency must be upper case: $currency" }
    }

    constructor(minor: Long) : this(minor, "EUR")                    // secondary: must delegate

    companion object {
        fun of(minor: Long, ccy: String) = Amount(minor, ccy.uppercase())   // normalize, then construct
        fun ofMajor(major: Long, ccy: String) = of(Math.multiplyExact(major, 100L), ccy)
    }
}

data class RangeK(val lo: Int, val hi: Int) : Serializable {
    init { require(lo <= hi) { "lo > hi: $lo > $hi" } }
}

@JvmRecord                                                            // a real JVM record
data class RangeR(val lo: Int, val hi: Int) : Serializable {
    init { require(lo <= hi) { "lo > hi: $lo > $hi" } }
}

/** Every way of making a data class runs init... except Java deserialization of a plain data class. */
fun main() {
    println(Amount.of(1250, "eur"))
    println(Amount(5))
    println(Amount.ofMajor(3, "usd"))
    try { Amount(-1, "EUR") } catch (e: IllegalArgumentException) { println("IAE: ${e.message}") }

    for (range in listOf<Any>(RangeK(1, 5), RangeR(1, 5))) {
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

// the stream ends with the int fields (hi, then lo); swapping them turns (1, 5) into (5, 1)
private fun swapLastTwoInts(b: ByteArray) {
    val n = b.size
    for (i in 0 until 4) {
        val t = b[n - 8 + i]
        b[n - 8 + i] = b[n - 4 + i]
        b[n - 4 + i] = t
    }
}

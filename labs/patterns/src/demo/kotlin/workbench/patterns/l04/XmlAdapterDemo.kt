package workbench.patterns.l04

import java.io.IOException

// An old courier client adapted to our port, plus a lambda adapter for a one-method port.

// the port our shop code depends on
fun interface Courier { fun book(address: String, grams: Int): String }

// a client we can't change: XML text in, XML text out, IOException on failure
class OldCourierClient {
    @Throws(IOException::class)
    fun submit(xml: String): String {
        if ("Nowhere" in xml) throw IOException("courier office closed: 503")
        val grams = xml.substringAfter("grams='").substringBefore("' to=")
        return "<ok ref='R-$grams'/>"
    }
}

class CourierUnavailable(message: String, cause: Throwable) : RuntimeException(message, cause)

// the adapter: implements our port, holds the old client, translates both ways
class OldCourierAdapter(private val old: OldCourierClient) : Courier {
    override fun book(address: String, grams: Int): String {
        val xml = "<parcel grams='$grams' to='$address'/>"
        try {
            val answer = old.submit(xml)
            return answer.substringAfter("ref='").substringBefore("'")         // their format ends here
        } catch (e: IOException) {
            throw CourierUnavailable("courier unreachable", e)                 // our exception, not theirs
        }
    }
}

fun main() {
    val courier: Courier = OldCourierAdapter(OldCourierClient())
    println("booked, ref " + courier.book("12 Mill Lane", 2_500))
    try {
        courier.book("1 Nowhere Road", 2_500)
    } catch (e: Exception) {
        println("caller sees ${e.javaClass.simpleName}: ${e.message}")
    }
    // for a fun interface, a lambda is the adapter (SAM conversion)
    val quick = Courier { _, grams -> "QUICK-$grams" }
    println("lambda adapter: " + quick.book("3 Pier Street", 990))
}

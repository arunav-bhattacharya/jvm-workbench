package workbench.nio.l02

import java.nio.ByteBuffer
import kotlin.text.Charsets.US_ASCII

/** Walks a ByteBuffer through put, flip, get, compact and clear, printing its cursor after each step. */
private fun show(step: String, b: ByteBuffer) =
    println("%-20s pos=%-2d lim=%-2d cap=%-2d remaining=%d".format(step, b.position(), b.limit(), b.capacity(), b.remaining()))

fun main() {
    val b = ByteBuffer.allocate(16)
    show("allocate(16)", b)
    b.put("hello".toByteArray(US_ASCII))
    show("put(\"hello\")", b)
    b.flip()                                    // write mode -> read mode: limit = position, position = 0
    show("flip()", b)
    val two = ByteArray(2)
    b.get(two)
    show("get(2) -> \"${String(two, US_ASCII)}\"", b)
    b.compact()                                 // move the unread "llo" to the front, back to write mode
    show("compact()", b)
    b.put("XY".toByteArray(US_ASCII))
    show("put(\"XY\")", b)
    b.flip()
    show("flip()", b)
    val rest = ByteArray(b.remaining())
    b.get(rest)
    println("readable content: \"${String(rest, US_ASCII)}\"")

    val forgot = ByteBuffer.allocate(8)
    forgot.put(1).put(2)                        // no flip() before handing it to write()
    println("forgot flip(): remaining()=${forgot.remaining()}, so a write would send 6 stale bytes, not the 2 you put")

    val heap = ByteBuffer.allocate(64)
    val direct = ByteBuffer.allocateDirect(64)
    println("heap:   isDirect=${heap.isDirect} hasArray=${heap.hasArray()} ${heap.javaClass.name}")
    println("direct: isDirect=${direct.isDirect} hasArray=${direct.hasArray()} ${direct.javaClass.name}")
}

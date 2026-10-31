package workbench.concurrency.l04

class DeclineCounterKt {
    private val lock = Any()            // a private lock object, like `new Object()` in Java
    private var declines = 0

    fun recordDecline() {
        synchronized(lock) {            // a standard-library function, not a keyword
            declines++
        }
    }

    fun total(): Int = synchronized(lock) { declines }   // it returns the block's value
}

class HitCounterKt {
    private var hits = 0

    @Synchronized fun hit() { hits++ }  // like a Java synchronized method: locks `this`
    @Synchronized fun total() = hits
}

fun main() {
    val declines = DeclineCounterKt()
    val hits = HitCounterKt()
    val threads = List(8) {
        Thread {
            repeat(100_000) {
                declines.recordDecline()
                hits.hit()
            }
        }.apply { start() }
    }
    threads.forEach { it.join() }
    println("declines = ${declines.total()}, hits = ${hits.total()}")
}

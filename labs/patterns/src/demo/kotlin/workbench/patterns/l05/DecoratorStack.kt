package workbench.patterns.l05

// Two decorators around a busy courier line. Same pieces, two orders, two different behaviors.

fun interface Booker { fun book(grams: Int): String }

// the real line: busy twice, then it books the parcel
class BusyLine : Booker {
    private var calls = 0
    override fun book(grams: Int): String {
        check(++calls > 2) { "line busy, try #$calls" }
        return "BB-$grams"
    }
}

// decorator 1: logs every call that passes through it
class Logging(private val inner: Booker, private val log: MutableList<String>) : Booker {
    override fun book(grams: Int): String {
        log += "book $grams"
        return inner.book(grams)
    }
}

// decorator 2: tries up to `attempts` times
class Retrying(private val inner: Booker, private val attempts: Int) : Booker {
    override fun book(grams: Int): String {
        var last: RuntimeException? = null
        repeat(attempts) {
            try {
                return inner.book(grams)
            } catch (e: RuntimeException) {
                last = e
            }
        }
        throw last!!
    }
}

fun main() {
    val log = mutableListOf<String>()
    val retryOutside = Retrying(Logging(BusyLine(), log), 3)
    println("Retrying(Logging(line)): ${retryOutside.book(1_250)}, log lines: ${log.size}")

    log.clear()
    val logOutside = Logging(Retrying(BusyLine(), 3), log)
    println("Logging(Retrying(line)): ${logOutside.book(1_250)}, log lines: ${log.size}")
}

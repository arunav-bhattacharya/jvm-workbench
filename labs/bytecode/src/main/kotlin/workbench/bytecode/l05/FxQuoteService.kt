package workbench.bytecode.l05

/**
 * A plain Kotlin service class with no interface. The tests wrap it in Byte Buddy subclass proxies.
 *
 * Kotlin classes and their members are final unless you say otherwise, and a subclass can't
 * override what is final. Make this class and the three quote methods `open`. Leave [deskName]
 * final on purpose: the tests check what a proxy does with a method it can't override.
 */
class FxQuoteService {
    /** Set after construction, the way a container injects a dependency. */
    var desk: String = "unset"

    /** Converts [amountMinor] at the pair's rate and adds the spread. Calls two methods on `this`. */
    fun quote(pair: String, amountMinor: Long): Long =
        amountMinor * rateMicros(pair) / 1_000_000 + spreadMinor(amountMinor)

    fun rateMicros(pair: String): Long = when (pair) {
        "EURUSD" -> 1_084_250L
        "GBPUSD" -> 1_270_400L
        else -> throw IllegalArgumentException("unknown pair $pair")
    }

    fun spreadMinor(amountMinor: Long): Long = amountMinor * 15 / 10_000

    /** Stays final in the solution too. */
    fun deskName(): String = "desk $desk"
}

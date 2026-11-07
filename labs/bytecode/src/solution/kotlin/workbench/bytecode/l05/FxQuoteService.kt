package workbench.bytecode.l05

// open: Byte Buddy (like CGLIB, ArC and Hibernate) can only subclass a non-final class
open class FxQuoteService {
    var desk: String = "unset"

    // open members: a subclass can only intercept what it can override
    open fun quote(pair: String, amountMinor: Long): Long =
        amountMinor * rateMicros(pair) / 1_000_000 + spreadMinor(amountMinor)

    open fun rateMicros(pair: String): Long = when (pair) {
        "EURUSD" -> 1_084_250L
        "GBPUSD" -> 1_270_400L
        else -> throw IllegalArgumentException("unknown pair $pair")
    }

    open fun spreadMinor(amountMinor: Long): Long = amountMinor * 15 / 10_000

    // still final: a proxy runs it on ITSELF, never intercepted and never forwarded
    fun deskName(): String = "desk $desk"
}

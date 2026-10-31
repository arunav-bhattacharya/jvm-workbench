package workbench.patterns.l05

// Two decorators around a flaky issuer. Same pieces, two orders, two different behaviors.

fun interface IssuerCall { fun authorize(amountMinor: Long): String }

// the real client: fails twice, then succeeds
class FlakyIssuer : IssuerCall {
    private var calls = 0
    override fun authorize(amountMinor: Long): String {
        check(++calls > 2) { "issuer timeout #$calls" }
        return "A-$amountMinor"
    }
}

// decorator 1: logs every call that passes through it
class Logging(private val inner: IssuerCall, private val log: MutableList<String>) : IssuerCall {
    override fun authorize(amountMinor: Long): String {
        log += "authorize $amountMinor"
        return inner.authorize(amountMinor)
    }
}

// decorator 2: tries up to `attempts` times
class Retrying(private val inner: IssuerCall, private val attempts: Int) : IssuerCall {
    override fun authorize(amountMinor: Long): String {
        var last: RuntimeException? = null
        repeat(attempts) {
            try {
                return inner.authorize(amountMinor)
            } catch (e: RuntimeException) {
                last = e
            }
        }
        throw last!!
    }
}

fun main() {
    val log = mutableListOf<String>()
    val retryOutside = Retrying(Logging(FlakyIssuer(), log), 3)
    println("Retrying(Logging(issuer)): ${retryOutside.authorize(1_250)}, log lines: ${log.size}")

    log.clear()
    val logOutside = Logging(Retrying(FlakyIssuer(), 3), log)
    println("Logging(Retrying(issuer)): ${logOutside.authorize(1_250)}, log lines: ${log.size}")
}

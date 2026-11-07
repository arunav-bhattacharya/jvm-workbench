package workbench.container.l02

import java.util.concurrent.atomic.AtomicInteger

class IssuerUnavailableException(message: String) : RuntimeException(message)

interface CardIssuerClient {
    @Timed
    @Retry(attempts = 3, on = [IssuerUnavailableException::class])
    fun authorize(pan: String, amountMinor: Long): String

    @Timed
    @Retry(attempts = 3, on = [IssuerUnavailableException::class])
    fun capture(authId: String): String

    /** A default method: each call inside it must go through the proxy on its own. */
    fun authorizeAndCapture(pan: String, amountMinor: Long): String = capture(authorize(pan, amountMinor))
}

/** What the fake issuer should do, and what it saw. A component, so a test gets it from the container. */
@Component
class IssuerScript {
    val authorizeFailures = AtomicInteger()          // fail this many authorize calls first
    val captureFailures = AtomicInteger()
    val authorizeCalls = AtomicInteger()
    val captureCalls = AtomicInteger()
    @Volatile var badCard = false                    // a failure that no retry can fix
}

/** A final Kotlin class: fine, because a JDK proxy needs only the interface. */
@Component
class FakeIssuer(private val script: IssuerScript) : CardIssuerClient {
    override fun authorize(pan: String, amountMinor: Long): String {
        script.authorizeCalls.incrementAndGet()
        if (script.badCard) throw IllegalArgumentException("card number fails the Luhn check")
        if (script.authorizeFailures.getAndDecrement() > 0) throw IssuerUnavailableException("issuer timed out")
        return "auth-${pan.takeLast(4)}"
    }

    override fun capture(authId: String): String {
        script.captureCalls.incrementAndGet()
        if (script.captureFailures.getAndDecrement() > 0) throw IssuerUnavailableException("issuer timed out")
        return "cap-$authId"
    }
}

/** No interface: intercepted with a subclass, so it must be open. */
@Component
open class RatesFetcher(private val script: IssuerScript) {
    val calls = AtomicInteger()

    @Retry(attempts = 4, on = [IssuerUnavailableException::class])
    open fun fetch(): String {
        if (calls.incrementAndGet() < 3) throw IssuerUnavailableException("rates feed down")
        return "EUR/USD 1.0870"
    }
}

/** Final, with an intercepted method: the container must refuse it. */
@Component
class FrozenFees {
    @Timed
    fun feeMinor(amountMinor: Long) = amountMinor * 29 / 1000
}

/** Open class, but the intercepted method was left final. */
@Component
open class HalfOpen {
    @Timed
    fun region() = "EU"
}

interface Pinger {
    fun ping(): String
}

/** The annotation sits on the class's method, where a JDK proxy never looks. */
@Component
class MisplacedTimed : Pinger {
    @Timed
    override fun ping() = "pong"
}

/** Nothing to intercept: it may stay final, and gets no proxy. */
@Component
class PlainFinal {
    fun hello() = "hi"
}

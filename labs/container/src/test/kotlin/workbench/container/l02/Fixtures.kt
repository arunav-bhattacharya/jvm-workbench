package workbench.container.l02

import java.util.concurrent.atomic.AtomicInteger

class BookingUnavailableException(message: String) : RuntimeException(message)

/** The box office's link to the city's booking service. */
interface BookingClient {
    @Timed
    @Retry(attempts = 3, on = [BookingUnavailableException::class])
    fun reserve(seat: String, priceCents: Long): String

    @Timed
    @Retry(attempts = 3, on = [BookingUnavailableException::class])
    fun confirm(holdId: String): String

    /** A default method: each call inside it must go through the proxy on its own. */
    fun reserveAndConfirm(seat: String, priceCents: Long): String = confirm(reserve(seat, priceCents))
}

/** What the fake booking service should do, and what it saw. A component, so a test gets it from the container. */
@Component
class BookingScript {
    val reserveFailures = AtomicInteger()            // fail this many reserve calls first
    val confirmFailures = AtomicInteger()
    val reserveCalls = AtomicInteger()
    val confirmCalls = AtomicInteger()
    @Volatile var badSeat = false                    // a failure that no retry can fix
}

/** A final Kotlin class: fine, because a JDK proxy needs only the interface. */
@Component
class FakeBooking(private val script: BookingScript) : BookingClient {
    override fun reserve(seat: String, priceCents: Long): String {
        script.reserveCalls.incrementAndGet()
        if (script.badSeat) throw IllegalArgumentException("no such seat: $seat")
        if (script.reserveFailures.getAndDecrement() > 0) throw BookingUnavailableException("booking service timed out")
        return "hold-$seat"
    }

    override fun confirm(holdId: String): String {
        script.confirmCalls.incrementAndGet()
        if (script.confirmFailures.getAndDecrement() > 0) throw BookingUnavailableException("booking service timed out")
        return "ticket-$holdId"
    }
}

/** No interface: intercepted with a subclass, so it must be open. */
@Component
open class ReviewFetcher(private val script: BookingScript) {
    val calls = AtomicInteger()

    @Retry(attempts = 4, on = [BookingUnavailableException::class])
    open fun fetch(): String {
        if (calls.incrementAndGet() < 3) throw BookingUnavailableException("reviews page down")
        return "4 stars"
    }
}

/** Final, with an intercepted method: the container must refuse it. */
@Component
class FrozenPrices {
    @Timed
    fun feeCents(priceCents: Long) = priceCents * 29 / 1000
}

/** Open class, but the intercepted method was left final. */
@Component
open class HalfOpen {
    @Timed
    fun hall() = "Main hall"
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

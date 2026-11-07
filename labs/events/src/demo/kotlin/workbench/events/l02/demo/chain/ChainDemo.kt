package workbench.events.l02.demo.chain

import workbench.events.l02.demo.PaymentCaptured
import workbench.events.l02.demo.PaymentEvent

// The event model (PaymentEvent and friends) is in DemoModel.kt, one package up.

fun interface Next { fun proceed(event: PaymentEvent): Int }
fun interface Middleware { fun intercept(event: PaymentEvent, next: Next): Int }
fun interface Handler { fun handle(event: PaymentEvent) }

/** Chain of responsibility: each middleware passes the event on, or answers 0 itself. */
fun chain(middleware: List<Middleware>, deliver: Next): Next =
    middleware.foldRight(deliver) { m, next -> Next { e -> m.intercept(e, next) } }

fun logging(name: String) = Middleware { event, next ->
    println("$name > ${event.paymentId}")
    val called = next.proceed(event)
    println("$name < ${event.paymentId}: $called handler(s)")
    called
}

fun dropDuplicates(): Middleware {
    val seen = HashSet<PaymentEvent>()
    return Middleware { event, next -> if (seen.add(event)) next.proceed(event) else 0 }
}

/** Decorator: the same Handler interface, plus timing. Virtual time keeps the output stable. */
var clock = 0L
fun tick(): Long { clock += 40_000; return clock }       // every read moves the clock by 40 microseconds

fun Handler.timed(name: String): Handler = Handler { event ->
    val start = tick()
    try { handle(event) } finally { println("    $name took ${(tick() - start) / 1_000} us") }
}

fun main() {
    val ledger = Handler { println("    ledger posts ${it.paymentId}") }.timed("ledger")
    val pipeline = chain(
        listOf(logging("outer"), dropDuplicates(), logging("inner")),   // Step 2: swap the first two
        Next { e -> ledger.handle(e); 1 },
    )
    val capture = PaymentCaptured("pay_7781", 1_999)
    pipeline.proceed(capture)
    println("-- the same capture again (a Kafka redelivery)")
    pipeline.proceed(capture.copy())
}

package workbench.events.l02.demo.chain

import workbench.events.l02.demo.ParcelCollected
import workbench.events.l02.demo.ParcelEvent

// The event model (ParcelEvent and friends) is in DemoModel.kt, one package up.

fun interface Next { fun proceed(event: ParcelEvent): Int }
fun interface Middleware { fun intercept(event: ParcelEvent, next: Next): Int }
fun interface Handler { fun handle(event: ParcelEvent) }

/** Chain of responsibility: each middleware passes the event on, or answers 0 itself. */
fun chain(middleware: List<Middleware>, deliver: Next): Next =
    middleware.foldRight(deliver) { m, next -> Next { e -> m.intercept(e, next) } }

fun logging(name: String) = Middleware { event, next ->
    println("$name > ${event.parcelId}")
    val called = next.proceed(event)
    println("$name < ${event.parcelId}: $called handler(s)")
    called
}

fun dropDuplicates(): Middleware {
    val seen = HashSet<ParcelEvent>()
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
    val load = Handler { println("    load board adds ${it.parcelId}") }.timed("load")
    val pipeline = chain(
        listOf(logging("outer"), dropDuplicates(), logging("inner")),   // Step 2: swap the first two
        Next { e -> load.handle(e); 1 },
    )
    val scan = ParcelCollected("PP-7781", 2_500)
    pipeline.proceed(scan)
    println("-- the same scan again (the scanner sent it twice)")
    pipeline.proceed(scan.copy())
}

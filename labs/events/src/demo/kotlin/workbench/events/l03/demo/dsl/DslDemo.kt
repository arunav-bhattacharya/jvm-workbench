package workbench.events.l03.demo.dsl

import java.util.concurrent.CopyOnWriteArrayList
import java.util.function.Consumer
import kotlin.reflect.KClass
import kotlin.reflect.cast

// A compact copy of the library: plain ids and cents, a flat-list bus, timing, and the DSL.

sealed interface PaymentEvent { val paymentId: String }
data class PaymentAuthorized(override val paymentId: String, val cents: Long) : PaymentEvent
data class PaymentCaptured(override val paymentId: String, val cents: Long) : PaymentEvent
data class PaymentRefunded(override val paymentId: String, val cents: Long) : PaymentEvent

fun interface Handler<in E : PaymentEvent> { fun handle(event: E) }
fun interface Subscription : AutoCloseable { override fun close() }

class Bus {
    private val handlers = CopyOnWriteArrayList<Pair<KClass<*>, Handler<PaymentEvent>>>()
    fun <E : PaymentEvent> subscribe(type: KClass<E>, handler: Handler<E>): Subscription {
        val entry = type to Handler<PaymentEvent> { handler.handle(type.cast(it)) }
        handlers += entry
        return Subscription { handlers -= entry }
    }
    fun publish(event: PaymentEvent) = handlers.filter { it.first.isInstance(event) }.forEach { it.second.handle(event) }
    fun handlerCount() = handlers.size
}

class Timings {
    var clock = 0L                                    // virtual time: each read moves it 2 ms
    val calls = mutableMapOf<String, Int>()
    val millis = mutableMapOf<String, Long>()
    fun tick(): Long { clock += 2_000_000; return clock }
}

fun <E : PaymentEvent> Handler<E>.timed(name: String, t: Timings): Handler<E> = Handler { e ->
    val start = t.tick()
    try { handle(e) } finally {
        t.calls.merge(name, 1) { a, b -> a + b }
        t.millis.merge(name, (t.tick() - start) / 1_000_000) { a, b -> a + b }
    }
}

@DslMarker
@Target(AnnotationTarget.CLASS)
annotation class EventsDsl

@EventsDsl
class SubscriptionsBuilder(private val bus: Bus, private val timings: Timings) {
    private val pending = mutableListOf<() -> Subscription>()
    fun <E : PaymentEvent> on(type: KClass<E>, handler: Handler<E>) { pending += { bus.subscribe(type, handler) } }
    fun <E : PaymentEvent> on(type: Class<E>, handler: Handler<E>) = on(type.kotlin, handler)
    inline fun <reified E : PaymentEvent> on(crossinline handler: (E) -> Unit) = on(E::class, Handler { handler(it) })
    fun timed(name: String, block: TimedGroup.() -> Unit) = TimedGroup(name, timings, this).block()
    fun commit(): Subscription {
        val handles = pending.map { it() }                // subscribe only after the block has finished
        return Subscription { handles.asReversed().forEach(Subscription::close) }
    }
}

@EventsDsl
class TimedGroup(private val name: String, private val timings: Timings, private val parent: SubscriptionsBuilder) {
    fun <E : PaymentEvent> on(type: KClass<E>, handler: Handler<E>) = parent.on(type, handler.timed(name, timings))
    fun <E : PaymentEvent> on(type: Class<E>, handler: Handler<E>) = on(type.kotlin, handler)
    inline fun <reified E : PaymentEvent> on(crossinline handler: (E) -> Unit) = on(E::class, Handler { handler(it) })
}

/** The Kotlin entry point. */
fun Bus.subscriptions(timings: Timings, block: SubscriptionsBuilder.() -> Unit): Subscription =
    SubscriptionsBuilder(this, timings).apply(block).commit()

/** The Java entry point: a Consumer, so Java lambdas need no return Unit.INSTANCE. */
object JavaDsl {
    @JvmStatic
    fun subscriptions(bus: Bus, timings: Timings, block: Consumer<SubscriptionsBuilder>): Subscription =
        bus.subscriptions(timings) { block.accept(this) }
}

fun main() {
    val bus = Bus()
    val timings = Timings()
    val handle = bus.subscriptions(timings) {
        on<PaymentEvent> { println("audit   ${it.paymentId} ${it::class.simpleName}") }
        timed("ledger") {
            on<PaymentCaptured> { println("ledger  +${it.cents}") }
            on<PaymentRefunded> { println("ledger  -${it.cents}") }
        }
    }
    bus.publish(PaymentCaptured("pay_7781", 1_999))
    bus.publish(PaymentRefunded("pay_7781", 500))
    bus.publish(PaymentAuthorized("pay_7782", 250))
    println("ledger: ${timings.calls["ledger"]} calls, ${timings.millis["ledger"]} ms; handlers: ${bus.handlerCount()}")

    handle.close()
    println("after close: ${bus.handlerCount()} handlers")

    try {
        bus.subscriptions(timings) {
            on<PaymentCaptured> { println("never subscribed") }
            error("missing configuration: ledger account")
        }
    } catch (e: IllegalStateException) {
        println("block failed (${e.message}); handlers: ${bus.handlerCount()}")
    }
}

package workbench.events.l03.demo.dsl

import java.util.concurrent.CopyOnWriteArrayList
import java.util.function.Consumer
import kotlin.reflect.KClass
import kotlin.reflect.cast

// A compact copy of the library: plain ids and grams, a flat-list bus, timing, and the DSL.

sealed interface ParcelEvent { val parcelId: String }
data class ParcelBooked(override val parcelId: String, val grams: Long) : ParcelEvent
data class ParcelCollected(override val parcelId: String, val grams: Long) : ParcelEvent
data class ParcelDelivered(override val parcelId: String, val grams: Long) : ParcelEvent

fun interface Handler<in E : ParcelEvent> { fun handle(event: E) }
fun interface Subscription : AutoCloseable { override fun close() }

class Bus {
    private val handlers = CopyOnWriteArrayList<Pair<KClass<*>, Handler<ParcelEvent>>>()
    fun <E : ParcelEvent> subscribe(type: KClass<E>, handler: Handler<E>): Subscription {
        val entry = type to Handler<ParcelEvent> { handler.handle(type.cast(it)) }
        handlers += entry
        return Subscription { handlers -= entry }
    }
    fun publish(event: ParcelEvent) = handlers.filter { it.first.isInstance(event) }.forEach { it.second.handle(event) }
    fun handlerCount() = handlers.size
}

class Timings {
    var clock = 0L                                    // virtual time: each read moves it 2 ms
    val calls = mutableMapOf<String, Int>()
    val millis = mutableMapOf<String, Long>()
    fun tick(): Long { clock += 2_000_000; return clock }
}

fun <E : ParcelEvent> Handler<E>.timed(name: String, t: Timings): Handler<E> = Handler { e ->
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
    fun <E : ParcelEvent> on(type: KClass<E>, handler: Handler<E>) { pending += { bus.subscribe(type, handler) } }
    fun <E : ParcelEvent> on(type: Class<E>, handler: Handler<E>) = on(type.kotlin, handler)
    inline fun <reified E : ParcelEvent> on(crossinline handler: (E) -> Unit) = on(E::class, Handler { handler(it) })
    fun timed(name: String, block: TimedGroup.() -> Unit) = TimedGroup(name, timings, this).block()
    fun commit(): Subscription {
        val handles = pending.map { it() }                // subscribe only after the block has finished
        return Subscription { handles.asReversed().forEach(Subscription::close) }
    }
}

@EventsDsl
class TimedGroup(private val name: String, private val timings: Timings, private val parent: SubscriptionsBuilder) {
    fun <E : ParcelEvent> on(type: KClass<E>, handler: Handler<E>) = parent.on(type, handler.timed(name, timings))
    fun <E : ParcelEvent> on(type: Class<E>, handler: Handler<E>) = on(type.kotlin, handler)
    inline fun <reified E : ParcelEvent> on(crossinline handler: (E) -> Unit) = on(E::class, Handler { handler(it) })
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
        on<ParcelEvent> { println("tracking ${it.parcelId} ${it::class.simpleName}") }
        timed("load") {
            on<ParcelCollected> { println("load     +${it.grams} g") }
            on<ParcelDelivered> { println("load     -${it.grams} g") }
        }
    }
    bus.publish(ParcelCollected("PP-7781", 2_500))
    bus.publish(ParcelDelivered("PP-7781", 2_500))
    bus.publish(ParcelBooked("PP-7782", 1_200))
    println("load: ${timings.calls["load"]} calls, ${timings.millis["load"]} ms; handlers: ${bus.handlerCount()}")

    handle.close()
    println("after close: ${bus.handlerCount()} handlers")

    try {
        bus.subscriptions(timings) {
            on<ParcelCollected> { println("never subscribed") }
            error("missing configuration: load limit")
        }
    } catch (e: IllegalStateException) {
        println("block failed (${e.message}); handlers: ${bus.handlerCount()}")
    }
}

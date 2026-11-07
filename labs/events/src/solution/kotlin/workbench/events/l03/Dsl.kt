package workbench.events.l03

import kotlin.reflect.KClass

/** Marks the subscription builders: inside a block, only the nearest builder is an implicit receiver. */
@DslMarker
@Target(AnnotationTarget.CLASS)
annotation class EventsDsl

/**
 * Collects subscriptions while the block runs, and subscribes them all only when it has finished.
 * A block that throws halfway subscribes nothing.
 */
@EventsDsl
class SubscriptionsBuilder private constructor(private val bus: EventBus, private val timings: Timings) {
    private val pending = mutableListOf<Pending<*>>()
    private var committed = false

    fun <E : PaymentEvent> on(type: KClass<E>, handler: Handler<E>) {
        // @DslMarker can't stop a call from inside a handler lambda (it has no receiver), so fail loudly
        check(!committed) { "this subscriptions block is already committed; subscribe from the block itself" }
        pending += Pending(type, handler)
    }

    /** For Java callers: b.on(PaymentRefunded.class, e -> ...). */
    fun <E : PaymentEvent> on(type: Class<E>, handler: Handler<E>) = on(type.kotlin, handler)

    // crossinline: the lambda is called from inside another object (the Handler), not from this body
    inline fun <reified E : PaymentEvent> on(crossinline handler: (E) -> Unit) = on(E::class, Handler { handler(it) })

    /** Every handler declared in [block] is timed under [name]. */
    fun timed(name: String, block: TimedGroup.() -> Unit) {
        TimedGroup(name, timings, this).block()
    }

    private fun commit(): Subscription {
        committed = true
        val handles = pending.map { it.subscribeTo(bus) }
        // one handle for the whole block; close in reverse order, like nested try-with-resources
        return Subscription { handles.asReversed().forEach(Subscription::close) }
    }

    // keeps E and the handler's type together, so subscribeTo needs no cast
    private class Pending<E : PaymentEvent>(val type: KClass<E>, val handler: Handler<E>) {
        fun subscribeTo(bus: EventBus): Subscription = bus.subscribe(type, handler)
    }

    companion object {
        /** Runs [block] on a new builder, then commits. Used by both entry points. */
        fun build(bus: EventBus, timings: Timings, block: SubscriptionsBuilder.() -> Unit): Subscription =
            SubscriptionsBuilder(bus, timings).apply(block).commit()
    }
}

/** The handlers declared inside timed(name) { ... }: each one is wrapped with the timing decorator. */
@EventsDsl
class TimedGroup(private val name: String, private val timings: Timings, private val parent: SubscriptionsBuilder) {
    fun <E : PaymentEvent> on(type: KClass<E>, handler: Handler<E>) = parent.on(type, handler.timed(name, timings))

    inline fun <reified E : PaymentEvent> on(crossinline handler: (E) -> Unit) = on(E::class, Handler { handler(it) })
}

/**
 * The Kotlin entry point:
 *
 *     val handle = bus.subscriptions(timings) {
 *         on<PaymentEvent> { audit(it) }
 *         timed("ledger") { on<PaymentCaptured> { ledger.credit(it) } }
 *     }
 */
fun EventBus.subscriptions(timings: Timings = Timings(), block: SubscriptionsBuilder.() -> Unit): Subscription =
    SubscriptionsBuilder.build(this, timings, block)

package workbench.events.l03

import kotlin.reflect.KClass

/**
 * Marks the subscription builders.
 *
 * TODO 2: annotate this class with @DslMarker, and put @EventsDsl on SubscriptionsBuilder and on
 * TimedGroup. Then a nested timed { } inside timed { } stops compiling instead of silently reaching
 * the outer builder.
 */
@Target(AnnotationTarget.CLASS)
annotation class EventsDsl

/**
 * Collects subscriptions while the block runs, and subscribes them all only when it has finished.
 * A block that throws halfway subscribes nothing.
 */
class SubscriptionsBuilder private constructor(private val bus: EventBus, private val timings: Timings) {
    private val pending = mutableListOf<Pending<*>>()
    private var committed = false

    /** TODO 3a: remember the subscription in `pending`. Don't subscribe yet. */
    fun <E : PaymentEvent> on(type: KClass<E>, handler: Handler<E>) {
        // @DslMarker can't stop a call from inside a handler lambda (it has no receiver), so fail loudly
        check(!committed) { "this subscriptions block is already committed; subscribe from the block itself" }
        TODO("add a Pending(type, handler)")
    }

    /** For Java callers: b.on(PaymentRefunded.class, e -> ...). */
    fun <E : PaymentEvent> on(type: Class<E>, handler: Handler<E>) = on(type.kotlin, handler)

    /**
     * TODO 4: the Kotlin shorthand, on<PaymentCaptured> { ... }. Call the KClass version with E::class and
     * Handler { handler(it) }. The compiler will ask you for one more modifier on `handler`: which, and why?
     */
    inline fun <reified E : PaymentEvent> on(handler: (E) -> Unit): Unit = TODO("on(E::class, Handler { handler(it) })")

    /** Every handler declared in [block] is timed under [name]. */
    fun timed(name: String, block: TimedGroup.() -> Unit) {
        TimedGroup(name, timings, this).block()
    }

    /**
     * TODO 3b: mark the builder committed, subscribe every pending entry (Pending.subscribeTo), and
     * return ONE Subscription that closes all of them, in reverse order.
     */
    private fun commit(): Subscription = TODO("subscribe everything, return one handle")

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
class TimedGroup(private val name: String, private val timings: Timings, private val parent: SubscriptionsBuilder) {
    /** TODO 5: wrap the handler with timed(name, timings) from Timing.kt and hand it to the parent builder. */
    fun <E : PaymentEvent> on(type: KClass<E>, handler: Handler<E>): Unit = TODO("parent.on(type, handler.timed(...))")

    /** TODO 5: the same shorthand as in SubscriptionsBuilder. */
    inline fun <reified E : PaymentEvent> on(handler: (E) -> Unit): Unit = TODO("on(E::class, Handler { handler(it) })")
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

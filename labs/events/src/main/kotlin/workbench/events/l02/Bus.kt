package workbench.events.l02

import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.CopyOnWriteArrayList
import kotlin.reflect.KClass
import kotlin.reflect.cast

/**
 * Takes one event.
 *
 * TODO 1: a handler only consumes E. Add the one word that lets a Handler<PaymentEvent> stand in
 * wherever a Handler<PaymentCaptured> is expected. (Java will then see Handler<? super E>.)
 */
fun interface Handler<E : PaymentEvent> {
    fun handle(event: E)
}

/** What subscribe returns. Closing it removes the handler; closing it again does nothing. */
fun interface Subscription : AutoCloseable {
    override fun close()
}

/** The rest of the chain: the next middleware, or delivery at the end. Returns how many handlers were called. */
fun interface Next {
    fun proceed(event: PaymentEvent): Int
}

/** One link in the chain around every publish: pass the event on with next.proceed, or return 0 to stop it. */
fun interface Middleware {
    fun intercept(event: PaymentEvent, next: Next): Int
}

/** Hears about every exception a handler throws. */
fun interface ErrorHandler {
    fun onError(event: PaymentEvent, error: Exception)

    companion object {
        val PRINT: ErrorHandler = ErrorHandler { event, error -> System.err.println("handler failed on $event: $error") }
    }
}

/**
 * An in-process event bus. publish delivers synchronously, on the caller's thread, to the handlers of
 * the event's class first and then to the handlers of each event supertype, nearest first.
 */
class EventBus(
    middleware: List<Middleware> = emptyList(),
    private val onError: ErrorHandler = ErrorHandler.PRINT,
) {
    // one list of adapters per subscribed type; copy-on-write, so delivery iterates a snapshot
    private val registry = ConcurrentHashMap<KClass<*>, CopyOnWriteArrayList<Handler<PaymentEvent>>>()

    // the dispatch keys of each event class, worked out once per class
    private val keyCache = ConcurrentHashMap<Class<*>, List<KClass<*>>>()

    // TODO 4: build the chain once. Fold a copy of `middleware` from the right, starting from
    // Next(::deliver), so that the first middleware wraps all the others. This version skips them all.
    private val pipeline: Next = Next(::deliver)

    /**
     * TODO 2: store an adapter, a Handler<PaymentEvent> that casts the event with type.cast and passes
     * it on, in the registry list for [type] (computeIfAbsent). Return a Subscription that removes
     * exactly that adapter.
     */
    fun <E : PaymentEvent> subscribe(type: KClass<E>, handler: Handler<E>): Subscription =
        TODO("store an adapter under type, return a handle that removes it")

    /** TODO 5: make this a one-line call to the other subscribe, with the real class of E. */
    inline fun <reified E : PaymentEvent> subscribe(handler: Handler<E>): Subscription =
        TODO("call subscribe(E::class, handler)")

    /** Runs the middleware chain, then delivers. Returns the number of handlers called. */
    fun publish(event: PaymentEvent): Int = pipeline.proceed(event)

    fun handlerCount(): Int = registry.values.sumOf { it.size }

    /**
     * TODO 3: for each key in dispatchKeys(event.javaClass), call every handler registered under it, in
     * order. Count the calls. If a handler throws an Exception, tell onError and carry on with the next.
     */
    private fun deliver(event: PaymentEvent): Int = TODO("deliver to every key's handlers, isolating failures")

    /** The event's class, then its supertypes that are events, nearest first. */
    private fun dispatchKeys(type: Class<*>): List<KClass<*>> = keyCache.computeIfAbsent(type) {
        val found = LinkedHashSet<Class<*>>()
        val queue = ArrayDeque<Class<*>>().apply { add(type) }
        while (queue.isNotEmpty()) {
            val c = queue.removeFirst()
            if (!PaymentEvent::class.java.isAssignableFrom(c) || !found.add(c)) continue
            queue.addAll(c.interfaces)                  // declaration order
            c.superclass?.let(queue::add)
        }
        found.map { it.kotlin }
    }
}

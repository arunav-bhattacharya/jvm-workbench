package workbench.events.l03

import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.CopyOnWriteArrayList
import kotlin.reflect.KClass
import kotlin.reflect.cast

/**
 * Takes one event. A handler only consumes E, so E is declared `in`: a Handler<PaymentEvent>
 * can stand in wherever a Handler<PaymentCaptured> is expected.
 */
fun interface Handler<in E : PaymentEvent> {
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
        @JvmField                                    // Java reads ErrorHandler.PRINT, not Companion.getPRINT()
        val PRINT: ErrorHandler = ErrorHandler { event, error -> System.err.println("handler failed on $event: $error") }
    }
}

/**
 * An in-process event bus. publish delivers synchronously, on the caller's thread, to the handlers of
 * the event's class first and then to the handlers of each event supertype, nearest first.
 */
class EventBus @JvmOverloads constructor(        // Java gets EventBus(), EventBus(list) and EventBus(list, onError)
    middleware: List<Middleware> = emptyList(),
    private val onError: ErrorHandler = ErrorHandler.PRINT,
) {
    // one list of adapters per subscribed type; copy-on-write, so delivery iterates a snapshot
    private val registry = ConcurrentHashMap<KClass<*>, CopyOnWriteArrayList<Handler<PaymentEvent>>>()

    // the dispatch keys of each event class, worked out once per class
    private val keyCache = ConcurrentHashMap<Class<*>, List<KClass<*>>>()

    // the chain, built once from a copy of the list: the first middleware wraps all the others,
    // and the last one wraps delivery
    private val pipeline: Next = middleware.toList()
        .foldRight(Next(::deliver)) { m, next -> Next { event -> m.intercept(event, next) } }

    fun <E : PaymentEvent> subscribe(type: KClass<E>, handler: Handler<E>): Subscription {
        // the adapter takes any event; the keys guarantee it is an E, and cast makes a routing bug loud
        val adapter = Handler<PaymentEvent> { event -> handler.handle(type.cast(event)) }
        val handlers = registry.computeIfAbsent(type) { CopyOnWriteArrayList() }
        handlers += adapter
        return Subscription { handlers.remove(adapter) }     // removes this adapter only, once
    }

    // not noinline: a Handler is an object, not a function type, so there is no lambda to inline
    inline fun <reified E : PaymentEvent> subscribe(handler: Handler<E>): Subscription = subscribe(E::class, handler)

    /**
     * For Java callers: bus.subscribe(PaymentCaptured.class, e -> ...). Java can't call the reified one.
     * TODO 1: one line. Turn the Class into a KClass and reuse the subscribe above.
     */
    fun <E : PaymentEvent> subscribe(type: Class<E>, handler: Handler<E>): Subscription =
        TODO("delegate to subscribe(KClass, Handler)")

    /** Runs the middleware chain, then delivers. Returns the number of handlers called. */
    fun publish(event: PaymentEvent): Int = pipeline.proceed(event)

    fun handlerCount(): Int = registry.values.sumOf { it.size }

    private fun deliver(event: PaymentEvent): Int {
        var called = 0
        for (key in dispatchKeys(event.javaClass)) {
            val handlers = registry[key] ?: continue
            for (handler in handlers) {                 // a snapshot: a handler may unsubscribe itself
                called++
                try {
                    handler.handle(event)
                } catch (e: Exception) {
                    onError.onError(event, e)           // one failing handler must not starve the rest
                }
            }
        }
        return called
    }

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

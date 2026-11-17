package workbench.events.l02.demo.variance

import workbench.events.l02.demo.ParcelCollected
import workbench.events.l02.demo.ParcelDelivered
import workbench.events.l02.demo.ParcelEvent
import kotlin.reflect.KClass
import kotlin.reflect.cast

// The event model (ParcelEvent and friends) is in DemoModel.kt, one package up.

/** Step 2: delete the word `in` and run again. */
fun interface Handler<in E : ParcelEvent> {
    fun handle(event: E)
}

class Bus {
    private val handlers = mutableListOf<Pair<KClass<*>, Handler<ParcelEvent>>>()

    fun <E : ParcelEvent> subscribe(type: KClass<E>, handler: Handler<E>) {
        handlers += type to Handler { event -> handler.handle(type.cast(event)) }
    }

    fun publish(event: ParcelEvent) {
        for ((type, h) in handlers) if (type.isInstance(event)) h.handle(event)
    }
}

fun main() {
    val tracking = Handler<ParcelEvent> { println("tracking ${it.parcelId} (${it::class.simpleName})") }
    val load = Handler<ParcelCollected> { println("load     +${it.grams} g") }

    val bus = Bus()
    bus.subscribe(ParcelCollected::class, load)
    bus.subscribe(ParcelCollected::class, tracking)            // a handler of any event fits here
    val forCollections: Handler<ParcelCollected> = tracking    // the same subtyping, written out

    // Step 3: uncomment. A handler that only knows collections can't take every event.
    // val tooWide: Handler<ParcelEvent> = load

    bus.publish(ParcelCollected("PP-7781", 2_500))
    bus.publish(ParcelDelivered("PP-7781", 2_500))             // nobody subscribed to deliveries
    forCollections.handle(ParcelCollected("PP-7782", 1_200))

    // What Java callers see for subscribe:
    println(Bus::class.java.getMethod("subscribe", KClass::class.java, Handler::class.java).toGenericString())
}

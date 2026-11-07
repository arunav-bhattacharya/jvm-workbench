package workbench.events.l02.demo.variance

import workbench.events.l02.demo.PaymentCaptured
import workbench.events.l02.demo.PaymentEvent
import workbench.events.l02.demo.PaymentRefunded
import kotlin.reflect.KClass
import kotlin.reflect.cast

// The event model (PaymentEvent and friends) is in DemoModel.kt, one package up.

/** Step 2: delete the word `in` and run again. */
fun interface Handler<in E : PaymentEvent> {
    fun handle(event: E)
}

class Bus {
    private val handlers = mutableListOf<Pair<KClass<*>, Handler<PaymentEvent>>>()

    fun <E : PaymentEvent> subscribe(type: KClass<E>, handler: Handler<E>) {
        handlers += type to Handler { event -> handler.handle(type.cast(event)) }
    }

    fun publish(event: PaymentEvent) {
        for ((type, h) in handlers) if (type.isInstance(event)) h.handle(event)
    }
}

fun main() {
    val audit = Handler<PaymentEvent> { println("audit   ${it.paymentId} (${it::class.simpleName})") }
    val ledger = Handler<PaymentCaptured> { println("ledger  +${it.cents}") }

    val bus = Bus()
    bus.subscribe(PaymentCaptured::class, ledger)
    bus.subscribe(PaymentCaptured::class, audit)              // a handler of any event fits here
    val forCaptures: Handler<PaymentCaptured> = audit         // the same subtyping, written out

    // Step 3: uncomment. A handler that only knows captures can't take every event.
    // val tooWide: Handler<PaymentEvent> = ledger

    bus.publish(PaymentCaptured("pay_7781", 1_999))
    bus.publish(PaymentRefunded("pay_7781", 500))             // nobody subscribed to refunds
    forCaptures.handle(PaymentCaptured("pay_7782", 250))

    // What Java callers see for subscribe:
    println(Bus::class.java.getMethod("subscribe", KClass::class.java, Handler::class.java).toGenericString())
}

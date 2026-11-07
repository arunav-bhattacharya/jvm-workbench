package workbench.events.l03.demo.javaview

import java.util.concurrent.CopyOnWriteArrayList
import kotlin.reflect.KClass
import kotlin.reflect.cast

// A small Kotlin API, written the way Kotlin code is usually written, plus the pieces that make
// it pleasant from Java. JavaViewDemo.java calls it; JavaViewDemo.kt calls the same API from Kotlin.

@JvmInline
value class PaymentId(val value: String) {
    init { require(value.startsWith("pay_")) { "invalid payment id: '$value'" } }
    override fun toString(): String = value
}

@JvmInline
value class Money(val minor: Long) {
    init { require(minor >= 0) { "amount must not be negative: $minor" } }
    override fun toString(): String = "$minor cents"
}

data class PaymentCaptured(val paymentId: PaymentId, val amount: Money)

fun interface Handler<in E : Any> { fun handle(event: E) }

/** Defaults only: Java gets the all-defaults constructor and the full one, nothing in between. */
class PlainBus(val name: String = "payments", val strict: Boolean = false)

/** The same, with @JvmOverloads: Java also gets FriendlyBus(String). */
class FriendlyBus @JvmOverloads constructor(val name: String = "payments", val strict: Boolean = false)

object Registry {
    private val handlers = CopyOnWriteArrayList<Pair<KClass<*>, Handler<Any>>>()

    fun <E : Any> subscribe(type: KClass<E>, handler: Handler<E>) {
        handlers += type to Handler<Any> { handler.handle(type.cast(it)) }
    }

    /** Kotlin only: Java can't see a reified function. */
    inline fun <reified E : Any> subscribe(handler: Handler<E>) = subscribe(E::class, handler)

    /** For Java: a Class token, and @JvmStatic so it's Registry.subscribe(...), not Registry.INSTANCE.subscribe(...). */
    @JvmStatic
    fun <E : Any> subscribe(type: Class<E>, handler: Handler<E>) = subscribe(type.kotlin, handler)

    fun publish(event: Any) = handlers.filter { it.first.isInstance(event) }.forEach { it.second.handle(event) }

    /** Takes a value class, so its JVM name is mangled: Java can't call it. */
    fun describe(id: PaymentId): String = "payment $id"
}

/** The Java door for the model: plain String and long in and out, and the value classes still validate. */
object Events {
    @JvmStatic
    fun captured(paymentId: String, amountMinor: Long): PaymentCaptured = PaymentCaptured(PaymentId(paymentId), Money(amountMinor))

    @JvmStatic
    fun paymentId(event: PaymentCaptured): String = event.paymentId.value

    @JvmStatic
    fun amountMinor(event: PaymentCaptured): Long = event.amount.minor
}

package workbench.events.l03.demo.javaview

import java.util.concurrent.CopyOnWriteArrayList
import kotlin.reflect.KClass
import kotlin.reflect.cast

// A small Kotlin API, written the way Kotlin code is usually written, plus the pieces that make
// it pleasant from Java. JavaViewDemo.java calls it; JavaViewDemo.kt calls the same API from Kotlin.

@JvmInline
value class ParcelId(val value: String) {
    init { require(value.startsWith("PP-")) { "invalid parcel id: '$value'" } }
    override fun toString(): String = value
}

@JvmInline
value class Weight(val grams: Long) {
    init { require(grams >= 0) { "weight must not be negative: $grams" } }
    override fun toString(): String = "$grams g"
}

data class ParcelCollected(val parcelId: ParcelId, val weight: Weight)

fun interface Handler<in E : Any> { fun handle(event: E) }

/** Defaults only: Java gets the all-defaults constructor and the full one, nothing in between. */
class PlainBus(val name: String = "parcels", val strict: Boolean = false)

/** The same, with @JvmOverloads: Java also gets FriendlyBus(String). */
class FriendlyBus @JvmOverloads constructor(val name: String = "parcels", val strict: Boolean = false)

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
    fun describe(id: ParcelId): String = "parcel $id"
}

/** The Java door for the model: plain String and long in and out, and the value classes still validate. */
object Events {
    @JvmStatic
    fun collected(parcelId: String, grams: Long): ParcelCollected = ParcelCollected(ParcelId(parcelId), Weight(grams))

    @JvmStatic
    fun parcelId(event: ParcelCollected): String = event.parcelId.value

    @JvmStatic
    fun grams(event: ParcelCollected): Long = event.weight.grams
}

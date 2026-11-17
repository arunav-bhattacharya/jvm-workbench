package workbench.generics.l11

import kotlin.reflect.KClass

/**
 * The shop's board of delivery bells, a small event bus. Each kind of delivery rings its own bell,
 * and a bell calls every listener who asked to hear it. Items flow OUT of the deliveries (producers);
 * listeners take them IN (consumers).
 */
class BellBoard {
    // keys come from item::class, which is a KClass<out Fruit>
    private val bells = HashMap<KClass<out Fruit>, MutableList<(Fruit) -> Unit>>()

    /**
     * Adds [listener] to the bell for items of class [type].
     *
     * TODO 4: you can't add an (E) -> Unit to a list of (Fruit) -> Unit: a listener that only takes
     * apples can't be handed a lemon. Store an adapter instead: a (Fruit) -> Unit that calls
     * listener only when type.safeCast(item) is not null.
     */
    fun <E : Fruit> listen(type: KClass<E>, listener: (E) -> Unit) {
        TODO("getOrPut the list for type, add an adapter lambda")
    }

    /**
     * TODO 5: the Kotlin-friendly version, `board.listen<Apple> { ... }`. Make it inline with a
     * reified E and delegate with E::class. The listener is stored, not called, so mark it `noinline`.
     */
    fun <E : Fruit> listen(listener: (E) -> Unit) {
        TODO("inline + reified E + noinline listener, then listen(E::class, listener)")
    }

    /** TODO 6: rings the bell for item::class: calls its listeners in the order they joined, returns how many ran. */
    fun ring(item: Fruit): Int = TODO("look up item::class, call each listener")
}

package workbench.generics.l11

import kotlin.reflect.KClass
import kotlin.reflect.safeCast

class BellBoard {
    private val bells = HashMap<KClass<out Fruit>, MutableList<(Fruit) -> Unit>>()

    fun <E : Fruit> listen(type: KClass<E>, listener: (E) -> Unit) {
        // the adapter takes any Fruit and passes it on only if it really is an E
        bells.getOrPut(type) { mutableListOf() }.add { item -> type.safeCast(item)?.let(listener) }
    }

    // noinline: the lambda is stored in the map, so it must stay a real object
    inline fun <reified E : Fruit> listen(noinline listener: (E) -> Unit) = listen(E::class, listener)

    fun ring(item: Fruit): Int {
        val listeners = bells[item::class] ?: return 0
        for (l in listeners) l(item)
        return listeners.size
    }
}

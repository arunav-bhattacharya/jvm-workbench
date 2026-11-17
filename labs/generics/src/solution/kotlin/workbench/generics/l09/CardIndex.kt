package workbench.generics.l09

import kotlin.reflect.KClass
import kotlin.reflect.KType
import kotlin.reflect.cast
import kotlin.reflect.typeOf

class CardIndex {
    private val byClass = HashMap<KClass<*>, Any>()
    private val byType = HashMap<KType, Any>()

    // KClass<T> and impl: T are tied together, so register(Scale::class, PlainLabels()) won't compile
    fun <T : Any> register(type: KClass<T>, impl: T) {
        byClass[type] = impl
    }

    fun <T : Any> get(type: KClass<T>): T {
        val impl = byClass[type] ?: throw NoSuchElementException("no card for " + type.simpleName)
        return type.cast(impl)                      // KClass.cast: checked, needs no kotlin-reflect
    }

    inline fun <reified T : Any> get(): T = get(T::class)

    // a KType key keeps type arguments: typeOf<Shelf<Apple>>() != typeOf<Shelf<Lemon>>()
    fun registerTyped(type: KType, impl: Any) {
        byType[type] = impl
    }

    fun getTyped(type: KType): Any = byType[type] ?: throw NoSuchElementException("no card for $type")

    inline fun <reified T : Any> registerTyped(impl: T) = registerTyped(typeOf<T>(), impl)

    // Unchecked, but safe by construction: values only get in through registerTyped<T>,
    // which files each one under typeOf<T>(). So the value under typeOf<T>() is always a T.
    @Suppress("UNCHECKED_CAST")
    inline fun <reified T : Any> getTyped(): T = getTyped(typeOf<T>()) as T
}

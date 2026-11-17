package workbench.generics.l09

import kotlin.reflect.KClass
import kotlin.reflect.KType

/**
 * The shop's card index: one card per tool, filed under the tool's type, so `index.get<Scale>()`
 * finds the scale.
 *
 * Part 1 files cards under a KClass. That is enough for Scale and LabelPrinter.
 * Part 2 files cards under a KType, because Shelf<Apple> and Shelf<Lemon> share one KClass.
 */
class CardIndex {
    private val byClass = HashMap<KClass<*>, Any>()
    private val byType = HashMap<KType, Any>()

    // ---- Part 1: KClass keys ----

    /**
     * Files [impl] under [type]. A later card for the same class replaces the earlier one.
     * The signature makes the compiler check that impl really is a T.
     */
    fun <T : Any> register(type: KClass<T>, impl: T) {
        TODO("store impl under its KClass")
    }

    /**
     * The tool filed under [type]. Throws NoSuchElementException("no card for " + type.simpleName)
     * when there is none. Return it with `type.cast(...)`: a checked cast, no warning.
     */
    fun <T : Any> get(type: KClass<T>): T = TODO("look it up, then type.cast")

    /** TODO: the Kotlin-friendly lookup, `index.get<Scale>()`. Make it inline + reified, pass T::class. */
    fun <T : Any> get(): T = TODO("inline + reified, then get(T::class)")

    // ---- Part 2: KType keys ----

    /** Files [impl] under its full type, type arguments included, such as Shelf<Apple>. */
    fun registerTyped(type: KType, impl: Any) {
        TODO("store impl under its KType")
    }

    /**
     * The tool filed under exactly [type]. Throws NoSuchElementException("no card for " + type)
     * when there is none. A KType can't cast for you, so this returns Any; the reified wrapper casts.
     */
    fun getTyped(type: KType): Any = TODO("look it up by KType")

    /** TODO: `index.registerTyped<Shelf<Apple>>(shelf)`. Make it inline + reified and use typeOf<T>(). */
    fun <T : Any> registerTyped(impl: T) {
        TODO("inline + reified, then registerTyped(typeOf<T>(), impl)")
    }

    /**
     * TODO: `index.getTyped<Shelf<Apple>>()`. Make it inline + reified and use typeOf<T>().
     * The cast to T is unchecked, but it is safe by construction: the only way in is registerTyped<T>,
     * which files every value under typeOf<T>(). Say so in a comment next to @Suppress("UNCHECKED_CAST").
     */
    fun <T : Any> getTyped(): T = TODO("inline + reified, then getTyped(typeOf<T>()) as T")
}

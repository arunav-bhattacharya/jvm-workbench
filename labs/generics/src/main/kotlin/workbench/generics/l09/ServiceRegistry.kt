package workbench.generics.l09

import kotlin.reflect.KClass
import kotlin.reflect.KType

/**
 * Looks services up by their type: `registry.get<PaymentGateway>()`.
 *
 * Part 1 keys services by KClass. That is enough for PaymentGateway and FraudCheck.
 * Part 2 keys services by KType, because Repository<Payment> and Repository<Refund> share one KClass.
 */
class ServiceRegistry {
    private val byClass = HashMap<KClass<*>, Any>()
    private val byType = HashMap<KType, Any>()

    // ---- Part 1: KClass keys ----

    /**
     * Registers [impl] as the service for [type]. A later registration for the same class replaces it.
     * The signature makes the compiler check that impl really is a T.
     */
    fun <T : Any> register(type: KClass<T>, impl: T) {
        TODO("store impl under its KClass")
    }

    /**
     * The service registered for [type]. Throws NoSuchElementException("no service for " + type.simpleName)
     * when there is none. Return it with `type.cast(...)`: a checked cast, no warning.
     */
    fun <T : Any> get(type: KClass<T>): T = TODO("look it up, then type.cast")

    /** TODO: the Kotlin-friendly lookup, `registry.get<PaymentGateway>()`. Make it inline + reified, pass T::class. */
    fun <T : Any> get(): T = TODO("inline + reified, then get(T::class)")

    // ---- Part 2: KType keys ----

    /** Registers [impl] under its full type, type arguments included, such as Repository<Payment>. */
    fun registerTyped(type: KType, impl: Any) {
        TODO("store impl under its KType")
    }

    /**
     * The service registered under exactly [type]. Throws NoSuchElementException("no service for " + type)
     * when there is none. A KType can't cast for you, so this returns Any; the reified wrapper casts.
     */
    fun getTyped(type: KType): Any = TODO("look it up by KType")

    /** TODO: `registry.registerTyped<Repository<Payment>>(repo)`. Make it inline + reified and use typeOf<T>(). */
    fun <T : Any> registerTyped(impl: T) {
        TODO("inline + reified, then registerTyped(typeOf<T>(), impl)")
    }

    /**
     * TODO: `registry.getTyped<Repository<Payment>>()`. Make it inline + reified and use typeOf<T>().
     * The cast to T is unchecked, but it is safe by construction: the only way in is registerTyped<T>,
     * which files every value under typeOf<T>(). Say so in a comment next to @Suppress("UNCHECKED_CAST").
     */
    fun <T : Any> getTyped(): T = TODO("inline + reified, then getTyped(typeOf<T>()) as T")
}

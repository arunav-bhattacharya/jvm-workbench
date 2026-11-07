package workbench.generics.l11

import kotlin.reflect.KType

/**
 * A key that carries the type of its value. Two keys are equal when both the name AND the full type are
 * equal, so key<List<String>>("limits") and key<List<Long>>("limits") are different keys.
 *
 * Key is invariant in T on purpose. If it were `out T`, a Key<List<String>> could be used as a Key<Any>,
 * and set(key, 42) would put an Int where a List<String> belongs.
 */
data class Key<T>(val name: String, val type: KType)

/** TODO 7: build a key whose type is the full type T: make it inline + reified and use typeOf<T>(). */
fun <T> key(name: String): Key<T> = TODO("inline + reified, then Key(name, typeOf<T>())")

/**
 * Per-payment attributes of many types in one map, e.g. attributes[CURRENCIES] = listOf("EUR").
 * TODO 8: write the four operations.
 */
class Attributes {
    private val values = HashMap<Key<*>, Any?>()

    operator fun <T> set(key: Key<T>, value: T) {
        TODO("store it")
    }

    /** The value for [key], or null if none was set. The cast to T is unchecked but safe: only set puts values in. */
    operator fun <T> get(key: Key<T>): T? = TODO("look it up, cast to T? under @Suppress")

    fun <T> getOrDefault(key: Key<T>, default: T): T = TODO("the value if the key is present, else default")

    /** Removes the value for [key] and returns it, or null if there was none. */
    fun <T> remove(key: Key<T>): T? = TODO("remove it, cast to T?")
}

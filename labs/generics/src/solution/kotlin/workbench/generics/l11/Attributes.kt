package workbench.generics.l11

import kotlin.reflect.KType
import kotlin.reflect.typeOf

data class Key<T>(val name: String, val type: KType)

inline fun <reified T> key(name: String): Key<T> = Key(name, typeOf<T>())

class Attributes {
    private val values = HashMap<Key<*>, Any?>()

    operator fun <T> set(key: Key<T>, value: T) {
        values[key] = value
    }

    // Unchecked, but safe by construction: the only way in is set(key: Key<T>, value: T),
    // and Key is invariant, so the value stored under a Key<T> is always a T.
    @Suppress("UNCHECKED_CAST")
    operator fun <T> get(key: Key<T>): T? = values[key] as T?

    @Suppress("UNCHECKED_CAST")
    fun <T> getOrDefault(key: Key<T>, default: T): T = if (key in values) values[key] as T else default

    @Suppress("UNCHECKED_CAST")
    fun <T> remove(key: Key<T>): T? = values.remove(key) as T?
}

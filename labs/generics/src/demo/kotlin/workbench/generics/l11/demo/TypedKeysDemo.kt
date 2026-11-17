package workbench.generics.l11.demo

import kotlin.reflect.KType
import kotlin.reflect.typeOf

/** Invariant on purpose: a Key<List<String>> is not a Key<Any>. */
data class Key<T>(val name: String, val type: KType)
inline fun <reified T> key(name: String) = Key<T>(name, typeOf<T>())

class Attributes {
    private val values = HashMap<Key<*>, Any?>()
    operator fun <T> set(key: Key<T>, value: T) { values[key] = value }
    @Suppress("UNCHECKED_CAST")                      // safe: only set(Key<T>, T) puts values in
    operator fun <T> get(key: Key<T>): T? = values[key] as T?
}

/** The same thing with `out T`: it compiles, and it is broken. */
data class LeakyKey<out T>(val name: String, val type: KType)
inline fun <reified T> leakyKey(name: String) = LeakyKey<T>(name, typeOf<T>())

class LeakyAttributes {
    private val values = HashMap<LeakyKey<*>, Any?>()
    operator fun <T> set(key: LeakyKey<T>, value: T) { values[key] = value }
    @Suppress("UNCHECKED_CAST")
    operator fun <T> get(key: LeakyKey<T>): T? = values[key] as T?
}

val VARIETIES = key<List<String>>("varieties")
val TOTAL = key<Int>("total grams")

fun main() {
    val attrs = Attributes()
    attrs[VARIETIES] = listOf("Gala", "Fuji")
    attrs[TOTAL] = 330
    val varieties: List<String>? = attrs[VARIETIES]    // typed by the key: no cast here
    println("varieties = $varieties, total = ${attrs[TOTAL]} g")

    val leaky = LeakyAttributes()
    val leakyVarieties = leakyKey<List<String>>("varieties")
    leaky[leakyVarieties] = 42                        // compiles: T is inferred as Any
    try {
        val first: String? = leaky[leakyVarieties]?.first()
        println(first)
    } catch (e: ClassCastException) {
        println("ClassCastException: ${e.message?.substringBefore(" (")}")
    }

    // Wrong move. Uncomment, predict the error, then run.
    // attrs[VARIETIES] = 42
}

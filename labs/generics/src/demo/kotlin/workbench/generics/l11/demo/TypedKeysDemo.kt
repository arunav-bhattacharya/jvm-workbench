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

val CURRENCIES = key<List<String>>("currencies")
val RETRIES = key<Int>("retries")

fun main() {
    val attrs = Attributes()
    attrs[CURRENCIES] = listOf("EUR", "USD")
    attrs[RETRIES] = 3
    val currencies: List<String>? = attrs[CURRENCIES]  // typed by the key: no cast here
    println("currencies = $currencies, retries = ${attrs[RETRIES]}")

    val leaky = LeakyAttributes()
    val leakyCurrencies = leakyKey<List<String>>("currencies")
    leaky[leakyCurrencies] = 42                       // compiles: T is inferred as Any
    try {
        val first: String? = leaky[leakyCurrencies]?.first()
        println(first)
    } catch (e: ClassCastException) {
        println("ClassCastException: ${e.message?.substringBefore(" (")}")
    }

    // Wrong move. Uncomment, predict the error, then run.
    // attrs[CURRENCIES] = 42
}

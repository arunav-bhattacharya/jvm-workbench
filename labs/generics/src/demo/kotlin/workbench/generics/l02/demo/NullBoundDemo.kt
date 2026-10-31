package workbench.generics.l02.demo

/** A tiny cache. get() returns null for "no entry". Is that always true? */
class Cache<K, V> {
    private val entries = HashMap<K, V>()
    fun put(key: K, value: V) { entries[key] = value }
    fun get(key: K): V? = entries[key]
}

fun main() {
    // V = String? is allowed, because the default bound of V is Any?
    val lastError = Cache<String, String?>()
    lastError.put("pay_1", null)          // "we checked, there was no error"

    println("pay_1 -> ${lastError.get("pay_1")}")      // stored null
    println("pay_9 -> ${lastError.get("pay_9")}")      // never stored
    println("Can you tell those two apart? Neither can the caller.")
}

package workbench.generics.l02.demo

/** A tiny cache. get() returns null for "no entry". Is that always true? */
class Cache<K, V> {
    private val entries = HashMap<K, V>()
    fun put(key: K, value: V) { entries[key] = value }
    fun get(key: K): V? = entries[key]
}

fun main() {
    // V = String? is allowed, because the default bound of V is Any?
    val problems = Cache<String, String?>()
    problems.put("apples", null)          // "we checked the apples: no problem"

    println("apples -> ${problems.get("apples")}")     // stored null
    println("figs -> ${problems.get("figs")}")         // never checked
    println("Can you tell those two apart? Neither can the caller.")
}

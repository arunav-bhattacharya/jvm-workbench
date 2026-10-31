package workbench.patterns.l05

// Decorators built with `by`: the compiler writes every forwarding method for you.

class CountingMap<K, V>(private val inner: MutableMap<K, V> = HashMap()) : MutableMap<K, V> by inner {
    var puts = 0
        private set

    override fun put(key: K, value: V): V? {
        puts++
        return inner.put(key, value)
    }
}

class CountingSet<E>(private val inner: MutableSet<E> = HashSet()) : MutableSet<E> by inner {
    var added = 0
        private set

    override fun add(element: E): Boolean {
        added++
        return inner.add(element)
    }

    override fun addAll(elements: Collection<E>): Boolean {
        added += elements.size
        return inner.addAll(elements)          // inner's addAll calls inner's add, never ours
    }
}

fun main() {
    val m = CountingMap<String, Int>()
    m["a"] = 1                                 // goes through our put
    m.putAll(mapOf("b" to 2, "c" to 3))        // forwarded to inner.putAll, which never calls our put
    println("CountingMap: puts=${m.puts}, size=${m.size}")

    val s = CountingSet<String>()
    s.addAll(listOf("x", "y", "z"))
    println("CountingSet: added=${s.added}, size=${s.size}")
}

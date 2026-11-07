package workbench.generics.l10.demo

/** Declared out, then the check is switched off for add(). It compiles. It is a lie. */
class Ledger<out T>(first: T) {
    private val entries = mutableListOf(first)
    fun add(entry: @UnsafeVariance T) { entries.add(entry) }
    fun last(): T = entries.last()
}

fun main() {
    // 1. The standard library uses @UnsafeVariance safely: contains only compares, it never stores.
    val amounts: List<Number> = listOf(1_200, 350)          // List<Int> seen as List<Number>
    println("contains(350): ${amounts.contains(350)}, contains(2.5): ${amounts.contains(2.5)}")

    // 2. And because contains takes an E, the compiler can catch a nonsense check.
    // println(listOf(1_200, 350).contains("1200"))         // wrong move 1

    // 3. Used carelessly, the same annotation breaks type safety.
    val ids: Ledger<String> = Ledger("pay_1")
    val anything: Ledger<Any> = ids                         // fine: Ledger is out T
    anything.add(42)                                        // compiles thanks to @UnsafeVariance
    try {
        val lastId: String = ids.last()
        println(lastId)
    } catch (e: ClassCastException) {
        println("ClassCastException: ${e.message?.substringBefore(" (")}")
    }
}

// Wrong move 2: remove @UnsafeVariance from a copy of Ledger and read the error.
// class Ledger2<out T> { fun add(entry: T) {} }

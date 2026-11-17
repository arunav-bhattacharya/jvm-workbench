package workbench.generics.l11.demo

interface Item<ID : Comparable<ID>> { val id: ID }
data class Supplier(override val id: Long, val name: String) : Item<Long>
data class Crate(override val id: String, val grams: Int) : Item<String>

/** The read side only hands T out, so it can be covariant: a glass display case. */
interface DisplayCase<out T> { fun findAll(): List<T> }

/** The full storeroom takes a T in save, so it stays invariant. */
interface Storeroom<T : Item<ID>, ID : Comparable<ID>> : DisplayCase<T> {
    fun save(item: T): T
}

/** A stock check that reads items of ANY kind. */
fun printAll(display: DisplayCase<Item<*>>) {
    for (item in display.findAll()) println("  item ${item.id}")
}

fun main() {
    val suppliers: DisplayCase<Supplier> = object : DisplayCase<Supplier> {
        override fun findAll() = listOf(Supplier(2, "Hill Farm"), Supplier(7, "Orchard Lane"))
    }
    val crates: DisplayCase<Crate> = object : DisplayCase<Crate> {
        override fun findAll() = listOf(Crate("c-1", 12_000))
    }
    println("suppliers:"); printAll(suppliers)       // a DisplayCase<Supplier> IS a DisplayCase<Item<*>>
    println("crates:"); printAll(crates)

    val storeroom: Storeroom<Supplier, Long> = object : Storeroom<Supplier, Long> {
        override fun save(item: Supplier) = item
        override fun findAll() = listOf(Supplier(9, "River Fields"))
    }
    println("the storeroom, through its display case:"); printAll(storeroom)   // the read side is still covariant

    // Wrong move. Uncomment, predict the error, then run.
    // val anyItem: Storeroom<Item<Long>, Long> = storeroom
}

package workbench.generics.l11

import java.util.TreeMap

interface Item<ID : Comparable<ID>> { val id: ID }

// only hands T out: covariant, so a DisplayCase<Supplier> is a DisplayCase<Item<*>>
interface DisplayCase<out T> {
    fun findAll(): List<T>
}

interface Storeroom<T : Item<ID>, ID : Comparable<ID>> : DisplayCase<T> {
    fun save(item: T): T
    fun findById(id: ID): T?
}

class InMemoryStoreroom<T : Item<ID>, ID : Comparable<ID>> : Storeroom<T, ID> {
    private val byId = TreeMap<ID, T>()                 // ID : Comparable<ID>, so it can be a sorted key

    override fun save(item: T): T { byId[item.id] = item; return item }
    override fun findById(id: ID): T? = byId[id]
    override fun findAll(): List<T> = byId.values.toList()
}

fun <T : Item<ID>, ID : Comparable<ID>> Storeroom<T, ID>.saveAll(items: Iterable<T>): List<T> = items.map { save(it) }

fun describeAll(display: DisplayCase<Item<*>>): List<String> = display.findAll().map { "item ${it.id}" }

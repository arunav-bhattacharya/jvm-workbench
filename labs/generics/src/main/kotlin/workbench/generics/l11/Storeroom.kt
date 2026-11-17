package workbench.generics.l11

/** Anything the storeroom keeps by id. */
interface Item<ID : Comparable<ID>> { val id: ID }

/**
 * The read side of the storeroom, like the glass display case: it only hands T out.
 * TODO 1: make it covariant, so a DisplayCase<Supplier> can be used as a DisplayCase<Item<*>>.
 */
interface DisplayCase<T> {
    fun findAll(): List<T>
}

/** The full storeroom reads AND writes T (save takes a T), so it stays invariant. */
interface Storeroom<T : Item<ID>, ID : Comparable<ID>> : DisplayCase<T> {
    fun save(item: T): T
    fun findById(id: ID): T?
}

/** TODO 2: keep the items in a sorted map by id. findAll returns them in id order. */
class InMemoryStoreroom<T : Item<ID>, ID : Comparable<ID>> : Storeroom<T, ID> {
    override fun save(item: T): T = TODO("store by id, return the item")
    override fun findById(id: ID): T? = TODO("look it up")
    override fun findAll(): List<T> = TODO("all items, sorted by id")
}

/** TODO 3: saves every item and returns them, in the order given. */
fun <T : Item<ID>, ID : Comparable<ID>> Storeroom<T, ID>.saveAll(items: Iterable<T>): List<T> =
    TODO("map each item through save")

/**
 * One line per item, "item <id>", in the order findAll returns them. It reads items of ANY kind,
 * which only works once DisplayCase is covariant (Java will then see DisplayCase<? extends Item<?>>).
 */
fun describeAll(display: DisplayCase<Item<*>>): List<String> =
    TODO("findAll, then \"item \${it.id}\"")

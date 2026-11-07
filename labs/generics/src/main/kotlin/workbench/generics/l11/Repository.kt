package workbench.generics.l11

/** Anything stored by id. */
interface Entity<ID : Comparable<ID>> { val id: ID }

/**
 * The read side of a repository: it only hands T out.
 * TODO 1: make it covariant, so a ReadRepository<Merchant> can be used as a ReadRepository<Entity<*>>.
 */
interface ReadRepository<T> {
    fun findAll(): List<T>
}

/** The full repository reads AND writes T (save takes a T), so it stays invariant. */
interface Repository<T : Entity<ID>, ID : Comparable<ID>> : ReadRepository<T> {
    fun save(entity: T): T
    fun findById(id: ID): T?
}

/** TODO 2: keep the entities in a sorted map by id. findAll returns them in id order. */
class InMemoryRepository<T : Entity<ID>, ID : Comparable<ID>> : Repository<T, ID> {
    override fun save(entity: T): T = TODO("store by id, return the entity")
    override fun findById(id: ID): T? = TODO("look it up")
    override fun findAll(): List<T> = TODO("all entities, sorted by id")
}

/** TODO 3: saves every item and returns them, in the order given. */
fun <T : Entity<ID>, ID : Comparable<ID>> Repository<T, ID>.saveAll(items: Iterable<T>): List<T> =
    TODO("map each item through save")

/**
 * One line per entity, "entity <id>", in the order findAll returns them. It reads entities of ANY kind,
 * which only works once ReadRepository is covariant (Java will then see ReadRepository<? extends Entity<?>>).
 */
fun describeAll(repo: ReadRepository<Entity<*>>): List<String> =
    TODO("findAll, then \"entity \${it.id}\"")

package workbench.generics.l11

import java.util.TreeMap

interface Entity<ID : Comparable<ID>> { val id: ID }

// only hands T out: covariant, so a ReadRepository<Merchant> is a ReadRepository<Entity<*>>
interface ReadRepository<out T> {
    fun findAll(): List<T>
}

interface Repository<T : Entity<ID>, ID : Comparable<ID>> : ReadRepository<T> {
    fun save(entity: T): T
    fun findById(id: ID): T?
}

class InMemoryRepository<T : Entity<ID>, ID : Comparable<ID>> : Repository<T, ID> {
    private val byId = TreeMap<ID, T>()                 // ID : Comparable<ID>, so it can be a sorted key

    override fun save(entity: T): T { byId[entity.id] = entity; return entity }
    override fun findById(id: ID): T? = byId[id]
    override fun findAll(): List<T> = byId.values.toList()
}

fun <T : Entity<ID>, ID : Comparable<ID>> Repository<T, ID>.saveAll(items: Iterable<T>): List<T> = items.map { save(it) }

fun describeAll(repo: ReadRepository<Entity<*>>): List<String> = repo.findAll().map { "entity ${it.id}" }

package workbench.generics.l11.demo

interface Entity<ID : Comparable<ID>> { val id: ID }
data class Merchant(override val id: Long, val name: String) : Entity<Long>
data class Settlement(override val id: String, val cents: Long) : Entity<String>

/** The read side only hands T out, so it can be covariant. */
interface ReadRepository<out T> { fun findAll(): List<T> }

/** The full repository takes a T in save, so it stays invariant. */
interface Repository<T : Entity<ID>, ID : Comparable<ID>> : ReadRepository<T> {
    fun save(entity: T): T
}

/** An audit job that reads entities of ANY kind. */
fun printAll(repo: ReadRepository<Entity<*>>) {
    for (e in repo.findAll()) println("  entity ${e.id}")
}

fun main() {
    val merchants: ReadRepository<Merchant> = object : ReadRepository<Merchant> {
        override fun findAll() = listOf(Merchant(2, "Bakery"), Merchant(7, "Kiosk"))
    }
    val settlements: ReadRepository<Settlement> = object : ReadRepository<Settlement> {
        override fun findAll() = listOf(Settlement("s-1", 1_200))
    }
    println("merchants:"); printAll(merchants)          // a ReadRepository<Merchant> IS a ReadRepository<Entity<*>>
    println("settlements:"); printAll(settlements)

    val writable: Repository<Merchant, Long> = object : Repository<Merchant, Long> {
        override fun save(entity: Merchant) = entity
        override fun findAll() = listOf(Merchant(9, "Florist"))
    }
    println("writable, through its read view:"); printAll(writable)   // the read side is still covariant

    // Wrong move. Uncomment, predict the error, then run.
    // val anyEntity: Repository<Entity<Long>, Long> = writable
}

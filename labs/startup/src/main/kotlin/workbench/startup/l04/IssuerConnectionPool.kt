package workbench.startup.l04

/**
 * A small pool of connections to the card issuer. It works, but it knows nothing about
 * checkpoints: its sockets are still open when the JVM is checkpointed, so the checkpoint fails.
 *
 * TODO:
 * - register the pool with [context] when it is created,
 * - [beforeCheckpoint]: close every socket and empty the pool,
 * - [afterRestore]: open [size] new sockets to [peer].
 */
class IssuerConnectionPool(
    private val network: FakeNetwork,
    private val size: Int,
    context: SimContext,
    private val peer: String = "issuer.example:443",
) : Resource {
    private val sockets = mutableListOf<FakeSocket>()
    private var next = 0

    init {
        repeat(size) { sockets += network.open(peer) }
    }

    /** The next connection, round-robin. */
    @Synchronized
    fun borrow(): FakeSocket {
        check(sockets.isNotEmpty()) { "pool is closed" }
        return sockets[next++ % sockets.size]
    }

    @Synchronized
    override fun beforeCheckpoint() {
        TODO("close every socket and empty the pool")
    }

    @Synchronized
    override fun afterRestore() {
        TODO("open size new sockets")
    }
}

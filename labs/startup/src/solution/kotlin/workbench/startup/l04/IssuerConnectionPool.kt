package workbench.startup.l04

/** A small pool of connections to the card issuer that closes and reopens them around a checkpoint. */
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
        context.register(this)               // 1. without this the hooks never run
    }

    /** The next connection, round-robin. */
    @Synchronized
    fun borrow(): FakeSocket {
        check(sockets.isNotEmpty()) { "pool is closed" }
        return sockets[next++ % sockets.size]
    }

    @Synchronized
    override fun beforeCheckpoint() {
        sockets.forEach { it.close() }       // 2. nothing open may go into the image
        sockets.clear()
    }

    @Synchronized
    override fun afterRestore() {
        repeat(size) { sockets += network.open(peer) }   // 3. brand-new connections after restore
        next = 0
    }
}

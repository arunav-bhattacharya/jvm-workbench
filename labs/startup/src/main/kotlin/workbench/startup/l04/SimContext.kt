package workbench.startup.l04

/**
 * A simulated CRaC global context. It follows the rules the org.crac docs give for the real one,
 * except that it keeps strong references (the real one keeps weak ones).
 *
 * TODO: implement [checkpointRestore]:
 * 1. Call `beforeCheckpoint()` on every registered resource in REVERSE registration order.
 *    An exception from one resource must not stop the others: catch it and keep it.
 * 2. Like CRaC's default file-descriptor policy (`error`), refuse to snapshot while any socket of
 *    [network] is still open: keep one `IllegalStateException` that names the open sockets.
 * 3. If step 1 or 2 found a problem: do NOT call [onSnapshot]. Call `afterRestore()` on every
 *    resource in registration order (catch and keep those exceptions too), then throw a
 *    [CheckpointException] with every kept exception added with `addSuppressed`.
 * 4. Otherwise call [onSnapshot], then `afterRestore()` on every resource in registration order.
 *    If any of those threw, throw a [RestoreException] with them suppressed.
 */
class SimContext(private val network: FakeNetwork, private val onSnapshot: () -> Unit = {}) {
    private val resources = mutableListOf<Resource>()

    @Synchronized
    fun register(resource: Resource) {
        resources += resource
    }

    @Synchronized
    fun checkpointRestore() {
        TODO("notify in reverse, check the sockets, snapshot, then restore in order")
    }
}

package workbench.startup.l04

/**
 * A simulated CRaC global context. It follows the rules the org.crac docs give for the real one,
 * except that it keeps strong references (the real one keeps weak ones).
 */
class SimContext(private val network: FakeNetwork, private val onSnapshot: () -> Unit = {}) {
    private val resources = mutableListOf<Resource>()

    @Synchronized
    fun register(resource: Resource) {
        resources += resource
    }

    @Synchronized
    fun checkpointRestore() {
        val problems = mutableListOf<Exception>()

        // 1. checkpoint notification: reverse registration order, everyone is told
        for (r in resources.asReversed()) {
            try {
                r.beforeCheckpoint()
            } catch (e: Exception) {
                problems += e
            }
        }

        // 2. the default fd policy is "error": an open socket fails the checkpoint
        val open = network.openSockets()
        if (open.isNotEmpty()) problems += IllegalStateException("open sockets at checkpoint: $open")

        if (problems.isNotEmpty()) {
            // 3. no image: restore notification starts at once, and everything is reported together
            restoreAll(problems)
            throw CheckpointException("checkpoint failed").apply { problems.forEach(::addSuppressed) }
        }

        // 4. the snapshot, then restore notification in registration order
        onSnapshot()
        val restoreProblems = mutableListOf<Exception>()
        restoreAll(restoreProblems)
        if (restoreProblems.isNotEmpty()) {
            throw RestoreException("restore failed").apply { restoreProblems.forEach(::addSuppressed) }
        }
    }

    private fun restoreAll(into: MutableList<Exception>) {
        for (r in resources) {
            try {
                r.afterRestore()
            } catch (e: Exception) {
                into += e
            }
        }
    }
}

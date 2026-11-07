package workbench.startup.l04

/**
 * The lab's copy of `org.crac.Resource`, without the `Context` parameter the real methods take.
 * A resource gets told before the JVM is checkpointed and after it is restored. Don't change it.
 */
interface Resource {
    /** Release what can't go into a snapshot: sockets, files, threads that talk to the outside. */
    fun beforeCheckpoint()

    /** Re-create what [beforeCheckpoint] released. */
    fun afterRestore()
}

/** Thrown when the checkpoint did not happen; each cause is a suppressed exception. */
class CheckpointException(message: String) : Exception(message)

/** Thrown when the snapshot was taken but some restore hooks failed; each cause is a suppressed exception. */
class RestoreException(message: String) : Exception(message)

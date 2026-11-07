package workbench.nio.l06

/** What a Quarkus REST endpoint method returns. */
enum class ReturnKind { PLAIN, UNI, MULTI, COMPLETION_STAGE, PUBLISHER, SUSPEND }

/** The annotations that change where Quarkus runs an endpoint. */
enum class Marker { BLOCKING, NON_BLOCKING, RUN_ON_VIRTUAL_THREAD, TRANSACTIONAL }

/** Where the endpoint method body runs. */
enum class Target { IO_THREAD, WORKER, VIRTUAL_THREAD }

/** A simplified endpoint signature: its name, return kind and annotations. */
data class Endpoint(val name: String, val returns: ReturnKind, val markers: Set<Marker> = emptySet())

/** Thrown when blocking code runs on an IO (event-loop) thread, like Quarkus's BlockingOperationNotAllowedException. */
class BlockingNotAllowedException(message: String) : IllegalStateException(message)

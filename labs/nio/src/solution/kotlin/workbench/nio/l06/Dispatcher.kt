package workbench.nio.l06

import io.vertx.core.Context
import io.vertx.core.Future
import io.vertx.core.Promise
import io.vertx.core.Vertx
import java.util.concurrent.Callable

object DispatchRules {
    private val nonBlockingReturns = setOf(
        ReturnKind.UNI, ReturnKind.MULTI, ReturnKind.COMPLETION_STAGE, ReturnKind.PUBLISHER, ReturnKind.SUSPEND,
    )

    fun target(endpoint: Endpoint): Target {
        val m = endpoint.markers
        return when {
            Marker.RUN_ON_VIRTUAL_THREAD in m -> Target.VIRTUAL_THREAD
            Marker.BLOCKING in m -> Target.WORKER              // explicit annotations win
            Marker.NON_BLOCKING in m -> Target.IO_THREAD
            Marker.TRANSACTIONAL in m -> Target.WORKER         // JTA blocks
            endpoint.returns in nonBlockingReturns -> Target.IO_THREAD   // "you promised not to block"
            else -> Target.WORKER                              // a plain return value: blocking style
        }
    }
}

object BlockingGuard {
    fun check(what: String) {
        // Quarkus asks its IO-thread detectors; for Vert.x that boils down to this check
        if (Context.isOnEventLoopThread()) throw BlockingNotAllowedException("Attempting $what on an IO thread")
    }
}

class Dispatcher(private val vertx: Vertx) {
    private val server: Context = vertx.getOrCreateContext()
    private val virtualThreads = Thread.ofVirtual().name("vt-endpoint-", 0)   // only used on the server's thread

    fun <T : Any> invoke(endpoint: Endpoint, body: () -> T): Future<T> {
        val promise: Promise<T> = Promise.promise()
        fun runBody() {
            try {
                promise.complete(body())
            } catch (e: Throwable) {
                promise.fail(e)
            }
        }
        server.runOnContext {                                        // the request arrives on the IO thread
            when (DispatchRules.target(endpoint)) {
                Target.IO_THREAD -> runBody()                        // stay: no thread switch
                Target.WORKER -> {
                    val task: Callable<T> = Callable { body() }
                    vertx.executeBlocking(task, false).onComplete(promise)   // unordered: calls from this context overlap
                }
                Target.VIRTUAL_THREAD -> virtualThreads.start { runBody() }   // a new one per call
            }
        }
        return promise.future()
    }
}

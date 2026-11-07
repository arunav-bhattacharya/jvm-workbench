package workbench.nio.l06

import io.vertx.core.Context
import io.vertx.core.Future
import io.vertx.core.Vertx

/**
 * Quarkus REST's dispatch rules (3.40), as this lab models them. First match wins:
 * 1. `RUN_ON_VIRTUAL_THREAD` -> VIRTUAL_THREAD
 * 2. `BLOCKING` -> WORKER, `NON_BLOCKING` -> IO_THREAD (an explicit annotation beats everything below)
 * 3. `TRANSACTIONAL` -> WORKER (3.40 docs: "JTA is a blocking technology")
 * 4. by return type: UNI, MULTI, COMPLETION_STAGE, PUBLISHER and SUSPEND -> IO_THREAD; PLAIN -> WORKER
 */
object DispatchRules {
    fun target(endpoint: Endpoint): Target = TODO("apply the four rules in order")
}

/** Guards blocking calls, like Quarkus does for JTA and blocking request-body reads. */
object BlockingGuard {
    /**
     * Throw `BlockingNotAllowedException("Attempting $what on an IO thread")` when the current
     * thread is a Vert.x event-loop thread (`io.vertx.core.Context.isOnEventLoopThread()`).
     * On any other thread, return normally.
     */
    fun check(what: String): Unit = TODO("throw on an event-loop thread")
}

/** Runs endpoint bodies where Quarkus would run them, on a plain Vert.x instance. */
class Dispatcher(private val vertx: Vertx) {
    /** Every request arrives here first, like an HTTP server's event-loop (IO) context in Quarkus. */
    private val server: Context = vertx.getOrCreateContext()

    /**
     * Receive the request on [server] (`server.runOnContext { ... }`), then run [body] on the thread
     * [DispatchRules.target] picks, and return a Future of its result:
     * - IO_THREAD: right there, on the server's event-loop thread
     * - WORKER: `vertx.executeBlocking(callable, false)`, so independent calls run in parallel
     * - VIRTUAL_THREAD: on a new virtual thread (`Thread.ofVirtual().start { ... }`)
     * If [body] throws, the Future fails with that exception.
     */
    fun <T : Any> invoke(endpoint: Endpoint, body: () -> T): Future<T> = TODO("dispatch on DispatchRules.target(endpoint)")
}

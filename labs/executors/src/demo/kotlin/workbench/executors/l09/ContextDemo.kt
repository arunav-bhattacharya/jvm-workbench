package workbench.executors.l09

import java.util.concurrent.Executors

private val requestId = ThreadLocal<String?>()

// capture on the submitting thread, install on the worker, always clean up
private fun withContext(task: () -> Unit): Runnable {
    val captured = requestId.get()
    return Runnable {
        val previous = requestId.get()
        requestId.set(captured)
        try {
            task()
        } finally {
            if (previous == null) requestId.remove() else requestId.set(previous)
        }
    }
}

/** A request id in a ThreadLocal, handed to a pool three ways. */
fun main() {
    Executors.newFixedThreadPool(1).use { pool ->
        requestId.set("req-42")
        pool.submit { println("1. plain task sees:   ${requestId.get()}") }.get()
        pool.submit(withContext { println("2. wrapped task sees: ${requestId.get()}") }).get()

        // a task that sets the ThreadLocal itself and forgets to remove it
        pool.submit { requestId.set("req-7") }.get()
        requestId.remove()                                                // the next caller has no request
        pool.submit { println("3. next task sees:    ${requestId.get()}  (left over from an earlier task)") }.get()
    }
}

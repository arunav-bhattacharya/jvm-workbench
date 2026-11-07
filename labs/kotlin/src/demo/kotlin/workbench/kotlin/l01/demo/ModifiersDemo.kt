package workbench.kotlin.l01.demo

import java.util.concurrent.Executor
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit

val listeners = mutableListOf<(String) -> Unit>()

/** noinline: `listener` is stored in a list, so it has to stay a real object. `log` is inlined. */
inline fun subscribe(log: (String) -> Unit, noinline listener: (String) -> Unit) {
    log("subscribing listener #${listeners.size + 1}")
    listeners += listener
}

/** crossinline: `task` runs inside a Runnable on another thread, so it may not return from the caller. */
inline fun runInBackground(executor: Executor, crossinline task: () -> Unit) {
    executor.execute { task() }
}

fun main() {
    subscribe({ println(it) }) { event -> println("listener got $event") }
    listeners.forEach { it("payment-captured") }

    val pool = Executors.newSingleThreadExecutor { Thread(it, "settlement-worker") }
    runInBackground(pool) { println("running on ${Thread.currentThread().name}") }
    pool.shutdown()
    pool.awaitTermination(5, TimeUnit.SECONDS)

    // Wrong moves, one at a time. Predict the error, run, then undo.
    // 1. Delete `noinline` in subscribe.
    // 2. Delete `crossinline` in runInBackground.
    // 3. Uncomment the next line.
    // runInBackground(pool) { return }
}

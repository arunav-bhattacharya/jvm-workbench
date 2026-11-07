package workbench.executors.l07

import java.util.concurrent.CompletableFuture
import java.util.concurrent.CompletionException
import java.util.concurrent.ExecutionException
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit

private fun describe(ex: Throwable): String {
    val name = ex.javaClass.simpleName
    return ex.cause?.let { "$name <- ${it.javaClass.simpleName}" } ?: name
}

private fun show(label: String, f: CompletableFuture<*>) {
    val seen = f.handle { _, ex -> describe(ex) }.join()
    println("%-42s %s".format(label, seen))
}

/** Which exception does each handler see? Predict every line before you run it. */
fun main() {
    val down = IllegalStateException("502")
    Executors.newFixedThreadPool(2, Thread.ofPlatform().name("io-", 1).factory()).use { io ->
        val supplied = CompletableFuture.supplyAsync<String>({ throw down }, io)
        val completed = CompletableFuture<String>()
        completed.completeExceptionally(down)
        val timedOut = CompletableFuture.supplyAsync({ Thread.sleep(1000); "late" }, io)
            .orTimeout(100, TimeUnit.MILLISECONDS)

        show("1. handle() on the supplyAsync future", supplied)
        show("2. handle() on completeExceptionally", completed)
        show("3. handle() one stage later", completed.thenApply { it.trim() })
        show("4. handle() after orTimeout", timedOut)
        try {
            supplied.get()
        } catch (e: ExecutionException) {
            println("%-42s %s".format("5. get() throws", describe(e)))
        }
        try {
            supplied.join()
        } catch (e: CompletionException) {
            println("%-42s %s".format("6. join() throws", describe(e)))
        }
    }
}

package workbench.executors.l06

import java.util.concurrent.CompletableFuture
import java.util.concurrent.Executors

private fun me(): String = Thread.currentThread().name

/** Which thread runs the next stage? It depends on timing, and on the Async suffix. */
fun main() {
    Executors.newFixedThreadPool(1, Thread.ofPlatform().name("io-", 1).factory()).use { io ->
        Executors.newFixedThreadPool(1, Thread.ofPlatform().name("cpu-", 1).factory()).use { cpu ->

            val done = CompletableFuture.completedFuture("x")
            println("1. thenApply on a finished future:    " + done.thenApply { me() }.join())

            val slow = CompletableFuture.supplyAsync({ Thread.sleep(200); "x" }, io)
            val attached = slow.thenApply { me() }                     // attached while slow still runs
            println("2. thenApply attached while running:  " + attached.join())

            println("3. thenApplyAsync(fn):                " + slow.thenApplyAsync { me() }.join())
            println("4. thenApplyAsync(fn, cpu):           " + slow.thenApplyAsync({ me() }, cpu).join())
        }
    }
}

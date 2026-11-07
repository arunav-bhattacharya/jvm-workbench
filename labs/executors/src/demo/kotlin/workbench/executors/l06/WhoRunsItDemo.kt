package workbench.executors.l06

import java.util.concurrent.CompletableFuture
import java.util.concurrent.Executors
import java.util.concurrent.ForkJoinPool

/** Which thread runs supplyAsync? Pass "1cpu" to size the common pool the way a 2-CPU container does. */
fun main(args: Array<String>) {
    if (args.firstOrNull() == "1cpu") {
        // must run before anything touches ForkJoinPool: a 2-CPU container gets parallelism 1
        System.setProperty("java.util.concurrent.ForkJoinPool.common.parallelism", "1")
    }
    println("JDK ${Runtime.version().feature()}, common pool parallelism ${ForkJoinPool.getCommonPoolParallelism()}")

    repeat(3) {
        val who = CompletableFuture.supplyAsync { Thread.currentThread().name }.join()
        println("supplyAsync(task)      ran on $who")
    }
    Executors.newFixedThreadPool(2, Thread.ofPlatform().name("io-", 1).factory()).use { io ->
        repeat(3) {
            val who = CompletableFuture.supplyAsync({ Thread.currentThread().name }, io).join()
            println("supplyAsync(task, io)  ran on $who")
        }
    }
}

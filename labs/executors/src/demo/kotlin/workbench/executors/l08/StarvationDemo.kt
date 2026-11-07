package workbench.executors.l08

import java.util.concurrent.CompletableFuture
import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors
import java.util.concurrent.ForkJoinPool
import java.util.concurrent.atomic.AtomicInteger
import java.util.stream.IntStream
import kotlin.concurrent.thread

private val T0 = System.nanoTime()
private val parallelism = ForkJoinPool.getCommonPoolParallelism()
private val started = AtomicInteger()
private val allBusy = CountDownLatch(1)

private fun log(msg: String) = println("%5d ms  %s".format((System.nanoTime() - T0) / 1_000_000, msg))

private fun lookup() {
    if (started.incrementAndGet() == parallelism + 1) allBusy.countDown()   // the common pool and main are all busy
    Thread.sleep(300)                                            // a remote call
}

private fun managedLookup() {
    // tells the pool this worker is about to block, so it can start a spare thread
    ForkJoinPool.managedBlock(object : ForkJoinPool.ManagedBlocker {
        var done = false
        override fun block(): Boolean {
            lookup()
            done = true
            return true
        }
        override fun isReleasable() = done
    })
}

/** Blocking BIN lookups in a parallel stream while a tiny task needs the common pool. Args: [blocking|managed|io]. */
fun main(args: Array<String>) {
    val mode = args.firstOrNull() ?: "blocking"
    val lookups = (parallelism + 1) * 4                          // four rounds of work for the common pool and main
    log("$mode: common pool parallelism $parallelism, $lookups lookups of 300 ms")

    val fx = thread {
        allBusy.await()                                          // start once the lookups are under way
        val t = System.nanoTime()
        val who = CompletableFuture.supplyAsync { Thread.currentThread().name }.join()   // a tiny task
        log("tiny task waited ${(System.nanoTime() - t) / 1_000_000} ms, then ran on $who")
    }

    if (mode == "io") {
        Executors.newFixedThreadPool(lookups).use { io ->
            val calls = (0 until lookups).map { CompletableFuture.runAsync(::lookup, io) }
            calls.forEach { it.join() }
        }
    } else {
        val managed = mode == "managed"
        IntStream.range(0, lookups).parallel().forEach { if (managed) managedLookup() else lookup() }
    }
    log("all lookups done")
    fx.join()
}

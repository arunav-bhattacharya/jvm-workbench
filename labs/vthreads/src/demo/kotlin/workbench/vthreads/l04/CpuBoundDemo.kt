package workbench.vthreads.l04

import java.security.MessageDigest
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors

/**
 * 64 CPU-bound tasks (each hashes the same 1 MB buffer many times, a fixed amount of work)
 * on a pool sized to the cores, then with one virtual thread per task.
 *
 * Args: number of tasks, hash rounds per task. Default: 64 20.
 */
private val data = ByteArray(1 shl 20)

fun main(args: Array<String>) {
    val tasks = args.getOrNull(0)?.toInt() ?: 64
    val rounds = args.getOrNull(1)?.toInt() ?: 20
    val cores = Runtime.getRuntime().availableProcessors()
    val work = Runnable { hashRounds(rounds) }
    hashRounds(rounds)                                   // warm up the JIT once

    timeTasks("fixed pool of $cores platform threads", Executors.newFixedThreadPool(cores), tasks, work)
    timeTasks("virtual thread per task", Executors.newVirtualThreadPerTaskExecutor(), tasks, work)
}

private fun timeTasks(label: String, executor: ExecutorService, tasks: Int, work: Runnable) {
    val t0 = System.nanoTime()
    executor.use { exec -> repeat(tasks) { exec.execute(work) } }
    println("%-34s %d tasks in %,5d ms".format(label, tasks, (System.nanoTime() - t0) / 1_000_000))
}

private fun hashRounds(rounds: Int): ByteArray {
    val sha = MessageDigest.getInstance("SHA-256")
    var out = ByteArray(0)
    repeat(rounds) { out = sha.digest(data) }            // pure CPU, never blocks
    return out
}

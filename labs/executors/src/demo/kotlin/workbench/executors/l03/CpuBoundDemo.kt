package workbench.executors.l03

import java.security.MessageDigest
import java.util.concurrent.Executors

// pure computation: SHA-256 over 16 MB, like signing a big settlement file. No I/O, no locks.
private fun hash(seed: Long): Long {
    val sha = MessageDigest.getInstance("SHA-256")
    val block = ByteArray(16 * 1024)
    block[0] = seed.toByte()
    repeat(1_000) { sha.update(block) }
    return sha.digest()[0].toLong()
}

/** The same CPU-bound job (32 hashing tasks) on pools of 1, 2, 4, 8 and 16 threads. */
fun main() {
    println("availableProcessors() = " + Runtime.getRuntime().availableProcessors())
    hash(1)                                             // warm up the JIT once
    for (threads in listOf(1, 2, 4, 8, 16)) {
        val t0 = System.nanoTime()
        val sum = Executors.newFixedThreadPool(threads).use { pool ->
            val parts = (0 until 32).map { task -> pool.submit<Long> { hash(task.toLong()) } }
            parts.sumOf { it.get() }
        }
        println("%2d threads: %,5d ms   (checksum %d)".format(threads, (System.nanoTime() - t0) / 1_000_000, sum))
    }
}

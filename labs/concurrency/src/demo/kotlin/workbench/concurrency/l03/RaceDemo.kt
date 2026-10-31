package workbench.concurrency.l03

import kotlin.concurrent.thread

// @Volatile only stops the JIT from keeping count in a register, which would hide the race.
// It does NOT make count++ safe. The memory model track explains why.
@Volatile
private var count = 0

/** Two threads each add 1,000,000 to a shared counter. Watch what comes out. */
fun main(args: Array<String>) {
    val perThread = args.firstOrNull()?.toInt() ?: 1_000_000
    for (run in 1..5) {
        count = 0
        val work = { repeat(perThread) { count++ } }
        val a = thread { work() }
        val b = thread { work() }
        a.join(); b.join()
        println("run %d: expected %,d, got %,d (lost %,d)".format(run, 2 * perThread, count, 2 * perThread - count))
    }
}

package workbench.jmm.l02

import kotlin.concurrent.thread

private val LEDGER_LOCK = Any()
private var balance = 0L   // meant to be guarded by LEDGER_LOCK

/** A writer sets a balance inside a lock. A reader spins until it sees it. Which lock does the reader need? */
fun main(args: Array<String>) {
    val shared = args.firstOrNull() == "shared"
    // daemon, so the JVM can exit even if the reader never stops
    val reader = thread(isDaemon = true) {
        if (shared) readWithLedgerLock() else readWithOwnLock()
    }

    Thread.sleep(500)          // let the JIT compile the reader's loop
    synchronized(LEDGER_LOCK) {
        balance = 12_000       // cents
    }
    println("writer set balance = 12000 inside synchronized(LEDGER_LOCK)")

    reader.join(3_000)
    println("reader still spinning 3 s later? ${reader.isAlive}")
}

private fun readWithOwnLock() {
    var seen: Long
    do {
        seen = synchronized(Any()) { balance }        // a lock no other thread can ever take
    } while (seen == 0L)
    println("reader (own lock) saw balance = $seen")
}

private fun readWithLedgerLock() {
    var seen: Long
    do {
        seen = synchronized(LEDGER_LOCK) { balance }  // the same monitor the writer released
    } while (seen == 0L)
    println("reader (LEDGER_LOCK) saw balance = $seen")
}

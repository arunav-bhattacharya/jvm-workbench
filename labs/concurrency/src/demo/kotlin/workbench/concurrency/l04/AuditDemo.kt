package workbench.concurrency.l04

import kotlin.concurrent.thread

// A transfer thread moves money under a lock. An auditor adds up the two balances, with or without it.
private val lock = Any()

// @Volatile only so the JIT re-reads the fields on every pass; it does not make the pair consistent
@Volatile private var a = 1_000L
@Volatile private var b = 1_000L

fun main(args: Array<String>) {
    val auditorLocks = args.firstOrNull() == "locked"
    val transfers = thread {
        repeat(200_000) {
            synchronized(lock) {        // debit and credit as one step
                a -= 50
                b += 50
            }
            synchronized(lock) {        // and move it back
                a += 50
                b -= 50
            }
        }
    }
    val auditor = thread {
        var audits = 0L
        var wrong = 0L
        while (transfers.isAlive) {
            val total = if (auditorLocks) {
                synchronized(lock) { a + b }
            } else {
                a + b                   // reads a, then b, while transfers may run in between
            }
            audits++
            if (total != 2_000L) wrong++
        }
        println("auditor %s the lock: %,d audits, %,d saw a total other than 2,000"
            .format(if (auditorLocks) "took" else "skipped", audits, wrong))
    }
    transfers.join()
    auditor.join()
}

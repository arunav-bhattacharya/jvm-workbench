package workbench.concurrency.l07

import java.util.concurrent.TimeUnit
import java.util.concurrent.locks.ReentrantLock
import kotlin.concurrent.thread
import kotlin.concurrent.withLock

// The end-of-day interest job holds the ledger lock for 1.5 s.
// Three threads want in, each in a different way.
private val ledger = ReentrantLock()
private val monitor = Any()                       // older code still guards the ledger with this

fun main() {
    val interest = thread(name = "interest") {
        ledger.withLock {
            synchronized(monitor) {               // the job holds the lock AND the monitor
                try { Thread.sleep(1_500) } catch (e: InterruptedException) { Thread.currentThread().interrupt() }
            }
        }
    }
    Thread.sleep(100)                             // let the interest job get in first

    val cashMachine = thread(start = false, name = "cash-machine") {
        val t0 = System.nanoTime()
        if (ledger.tryLock(200, TimeUnit.MILLISECONDS)) {          // wait at most 200 ms
            try { println("cash-machine: got the lock") } finally { ledger.unlock() }
        } else {
            println("cash-machine: gave up after %d ms, asked the customer to try again".format((System.nanoTime() - t0) / 1_000_000))
        }
    }

    val statement = thread(start = false, name = "statement") {
        try {
            ledger.lockInterruptibly()                             // an interrupt can cancel this wait
            try { println("statement: got the lock") } finally { ledger.unlock() }
        } catch (e: InterruptedException) {
            println("statement: interrupted while waiting, gave up cleanly")
        }
    }

    val teller = thread(start = false, name = "teller") {
        synchronized(monitor) {                                    // no way to give up here
            println("teller: got the monitor at last, interrupted=${Thread.currentThread().isInterrupted}")
        }
    }

    cashMachine.start()
    statement.start()
    teller.start()
    Thread.sleep(400)
    println("states: statement=${statement.state}, teller=${teller.state}")
    statement.interrupt()                         // the program is shutting down
    teller.interrupt()
    listOf(cashMachine, statement, teller, interest).forEach { it.join() }
}

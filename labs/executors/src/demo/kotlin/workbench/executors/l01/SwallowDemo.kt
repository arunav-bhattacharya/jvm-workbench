package workbench.executors.l01

import java.util.concurrent.ExecutionException
import java.util.concurrent.Executors

/** The same failing task, sent once with execute and once with submit. Watch where the exception goes. */
fun main() {
    Executors.newFixedThreadPool(1).use { pool ->
        val charge = Runnable {
            println("charging on " + Thread.currentThread().name)
            throw IllegalStateException("card issuer returned 502")
        }

        println("--- execute ---")
        pool.execute(charge)
        Thread.sleep(200)                       // give the stack trace time to print

        println("--- submit ---")
        val f = pool.submit(charge)
        Thread.sleep(200)
        println("submit: nothing printed. isDone=" + f.isDone)

        println("--- get ---")
        try {
            f.get()
        } catch (e: ExecutionException) {
            println("get() threw ExecutionException, cause: " + e.cause)
        }
    }
}

package workbench.executors.l01

import java.util.concurrent.ExecutionException
import java.util.concurrent.Executors

/** The same failing task, sent once with execute and once with submit. Watch where the exception goes. */
fun main() {
    Executors.newFixedThreadPool(1).use { pool ->
        val cook = Runnable {
            println("cooking on " + Thread.currentThread().name)
            throw IllegalStateException("out of eggs")
        }

        println("--- execute ---")
        pool.execute(cook)
        Thread.sleep(200)                       // give the stack trace time to print

        println("--- submit ---")
        val f = pool.submit(cook)
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

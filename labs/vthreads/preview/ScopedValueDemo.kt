// JDK 25 or later. Scoped values are final in JDK 25 (JEP 506). Needs the Kotlin command-line
// compiler. From labs/:
//     kotlinc vthreads/preview/ScopedValueDemo.kt -include-runtime -d vthreads/build/sv-demo.jar
//     java -jar vthreads/build/sv-demo.jar
// Not part of the Gradle build, because the labs compile for JDK 21, where ScopedValue is a preview API.

import java.util.concurrent.Callable
import java.util.concurrent.Executors

private val CUSTOMER_TL = ThreadLocal<String>()
private val CUSTOMER: ScopedValue<String> = ScopedValue.newInstance()

// deep in the call chain: reads the context, never sets it
private fun receiptLine() = "ThreadLocal=${CUSTOMER_TL.get()}, ScopedValue=${CUSTOMER.orElse("unbound")}"

fun main() {
    // 1. a ThreadLocal set on a pooled thread and never removed
    Executors.newFixedThreadPool(1).use { pool ->
        pool.submit(Callable {
            CUSTOMER_TL.set("ann")                              // forgot CUSTOMER_TL.remove()
            receiptLine()
        }).get()
        println("1. next task, same pool thread: " + pool.submit(Callable { receiptLine() }).get())
    }

    // 2. a scoped value is bound for one call, and gone afterwards
    // Runnable { } is optional; it shows this is the binding's run, not Kotlin's run {}
    ScopedValue.where(CUSTOMER, "ann").run(Runnable { println("2. inside run():   " + receiptLine()) })
    println("   after run():    " + receiptLine())

    // 3. rebind for a nested call; the outer binding comes back when it returns
    ScopedValue.where(CUSTOMER, "ann").run(Runnable {
        ScopedValue.where(CUSTOMER, "ben").run(Runnable { println("3. nested:         " + receiptLine()) })
        println("   outer again:    " + receiptLine())
    })

    // 4. a thread you start yourself does not inherit the binding
    ScopedValue.where(CUSTOMER, "ann").run(Runnable {
        val child = Thread.ofVirtual().start { println("4. plain thread:   " + receiptLine()) }
        child.join()
    })
}

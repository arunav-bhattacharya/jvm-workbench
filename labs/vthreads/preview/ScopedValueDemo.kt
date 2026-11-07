// JDK 25 or later. Scoped values are final in JDK 25 (JEP 506). Needs the Kotlin command-line
// compiler. From labs/vthreads:
//     kotlinc preview/ScopedValueDemo.kt -include-runtime -d build/sv-demo.jar
//     java -jar build/sv-demo.jar
// Not part of the Gradle build, because the labs compile for JDK 21, where ScopedValue is a preview API.

import java.util.concurrent.Callable
import java.util.concurrent.Executors

private val TENANT_TL = ThreadLocal<String>()
private val TENANT: ScopedValue<String> = ScopedValue.newInstance()

// deep in the call chain: reads the context, never sets it
private fun ledgerLookup() = "ThreadLocal=${TENANT_TL.get()}, ScopedValue=${TENANT.orElse("unbound")}"

fun main() {
    // 1. a ThreadLocal set on a pooled thread and never removed
    Executors.newFixedThreadPool(1).use { pool ->
        pool.submit(Callable {
            TENANT_TL.set("bank-a")                             // forgot TENANT_TL.remove()
            ledgerLookup()
        }).get()
        println("1. next task, same pool thread: " + pool.submit(Callable { ledgerLookup() }).get())
    }

    // 2. a scoped value is bound for one call, and gone afterwards
    // (Runnable { } picks ScopedValue.Carrier.run, not Kotlin's own run)
    ScopedValue.where(TENANT, "bank-a").run(Runnable { println("2. inside run():   " + ledgerLookup()) })
    println("   after run():    " + ledgerLookup())

    // 3. rebind for a nested call; the outer binding comes back when it returns
    ScopedValue.where(TENANT, "bank-a").run(Runnable {
        ScopedValue.where(TENANT, "bank-b").run(Runnable { println("3. nested:         " + ledgerLookup()) })
        println("   outer again:    " + ledgerLookup())
    })

    // 4. a thread you start yourself does not inherit the binding
    ScopedValue.where(TENANT, "bank-a").run(Runnable {
        val child = Thread.ofVirtual().start { println("4. plain thread:   " + ledgerLookup()) }
        child.join()
    })
}

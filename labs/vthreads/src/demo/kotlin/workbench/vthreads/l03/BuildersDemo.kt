package workbench.vthreads.l03

import java.util.concurrent.Callable
import java.util.concurrent.Executors

/** Every way to start a virtual thread in JDK 21+, called from Kotlin, with what each one prints. */
private fun show(how: String) {
    val t = Thread.currentThread()
    println("%-34s name=%-10s virtual=%-5s daemon=%s".format(how, "'${t.name}'", t.isVirtual, t.isDaemon))
}

fun main() {
    // 1. the shortcut: start one now, no name
    Thread.startVirtualThread { show("Thread.startVirtualThread") }.join()

    // 2. the builder: name it, then start it
    Thread.ofVirtual().name("auth-7").start { show("Thread.ofVirtual().name().start") }.join()

    // 3. unstarted: create now, start later
    val c = Thread.ofVirtual().unstarted { show("Thread.ofVirtual().unstarted") }
    c.start()
    c.join()

    // 4. a factory with numbered names, for code that wants a ThreadFactory
    val factory = Thread.ofVirtual().name("ledger-", 0).factory()
    Executors.newThreadPerTaskExecutor(factory).use { named ->
        repeat(2) { named.submit { show("newThreadPerTaskExecutor(factory)") } }
    }

    // 5. the one you'll use most: a new virtual thread per task, closed with use {}
    Executors.newVirtualThreadPerTaskExecutor().use { perTask ->
        val f = perTask.submit(Callable {
            show("newVirtualThreadPerTaskExecutor")
            "approved"
        })
        println("future result: ${f.get()}")
    }   // close() waits for every task submitted above
}

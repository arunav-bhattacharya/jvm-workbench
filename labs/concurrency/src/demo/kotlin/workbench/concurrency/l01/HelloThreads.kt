package workbench.concurrency.l01

// Lists the threads the JVM already has, then starts two of your own. Run it a few times.
fun main() {
    println("cores the JVM sees: ${Runtime.getRuntime().availableProcessors()}")
    println("Java threads before main starts any:")
    for (t in Thread.getAllStackTraces().keys) {
        println("  ${t.name}${if (t.isDaemon) " (daemon)" else ""}")
    }

    val task = Runnable { println("hello from ${Thread.currentThread().name}") }
    val a = Thread(task, "worker-a")
    val b = Thread(task, "worker-b")

    a.start()          // try changing these two calls to a.run() and b.run()
    b.start()

    a.join()           // wait for both to finish before main goes on
    b.join()
    println("main is done")
}

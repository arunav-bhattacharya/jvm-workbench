package workbench.nio.l01

import java.io.IOException
import java.lang.management.ManagementFactory
import java.net.InetAddress
import java.net.ServerSocket
import java.net.Socket
import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import kotlin.concurrent.thread

/**
 * Opens N idle connections to a blocking server and counts what they cost.
 * Args: [clients, default 2000] [seconds to hold the connections open, default 0]
 */
fun main(args: Array<String>) {
    val clients = args.getOrNull(0)?.toInt() ?: 2_000
    val holdSeconds = args.getOrNull(1)?.toInt() ?: 0
    runIdleClients("platform thread per connection", Executors.newCachedThreadPool(), clients, holdSeconds)
    runIdleClients("virtual thread per connection", Executors.newVirtualThreadPerTaskExecutor(), clients, holdSeconds)
}

private fun runIdleClients(label: String, handlers: ExecutorService, clients: Int, holdSeconds: Int) {
    val mx = ManagementFactory.getThreadMXBean()   // counts platform threads only
    val before = mx.threadCount
    val handlerThreads = CopyOnWriteArrayList<Thread>()
    ServerSocket(0, clients, InetAddress.getLoopbackAddress()).use { server ->
        thread(isDaemon = true, name = "acceptor") {
            try {
                while (true) {
                    val s = server.accept()
                    handlers.execute {
                        handlerThreads += Thread.currentThread()
                        try {
                            s.use { it.getInputStream().read() }   // blocks until the client sends a byte or closes
                        } catch (_: IOException) {
                        }
                    }
                }
            } catch (_: IOException) {
                // server closed
            }
        }

        val t0 = System.nanoTime()
        val open = List(clients) { Socket(InetAddress.getLoopbackAddress(), server.localPort) }
        while (handlerThreads.size < clients) Thread.sleep(10)
        println("%s: %,d idle clients connected in %,d ms".format(label, clients, (System.nanoTime() - t0) / 1_000_000))
        println("   platform threads: $before before, ${mx.threadCount} now")
        println("   a handler blocked in read() reports state ${handlerThreads.first().state}")
        if (holdSeconds > 0) {
            println("   holding the connections for $holdSeconds s (pid ${ProcessHandle.current().pid()})")
            Thread.sleep(holdSeconds * 1_000L)
        }
        open.forEach { it.close() }
    }
    handlers.shutdown()
    handlers.awaitTermination(5, TimeUnit.SECONDS)
}

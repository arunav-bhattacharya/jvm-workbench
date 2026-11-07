package workbench.nio.l07

import org.eclipse.jetty.io.Content
import org.eclipse.jetty.server.Handler
import org.eclipse.jetty.server.Request
import org.eclipse.jetty.server.Response
import org.eclipse.jetty.server.Server
import org.eclipse.jetty.server.ServerConnector
import org.eclipse.jetty.util.Callback
import org.eclipse.jetty.util.VirtualThreads
import org.eclipse.jetty.util.thread.QueuedThreadPool
import org.eclipse.jetty.util.thread.ThreadPool
import org.eclipse.jetty.util.thread.VirtualThreadPool
import java.net.URI
import java.net.http.HttpClient
import java.net.http.HttpRequest
import java.net.http.HttpResponse
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger

/** 40 concurrent requests to a handler that blocks 300 ms, on three kinds of thread pool. */
private val loadClient = HttpClient.newBuilder().proxy(HttpClient.Builder.NO_PROXY).version(HttpClient.Version.HTTP_1_1).build()

private class KtSlowLedger : Handler.Abstract() {
    val inFlight = AtomicInteger()
    val max = AtomicInteger()

    override fun handle(request: Request, response: Response, callback: Callback): Boolean {
        max.accumulateAndGet(inFlight.incrementAndGet()) { a, b -> maxOf(a, b) }
        try {
            Thread.sleep(300)                                       // the "JDBC call"
        } finally {
            inFlight.decrementAndGet()
        }
        Content.Sink.write(response, true, "ok", callback)
        return true
    }
}

private fun runLoad(label: String, pool: ThreadPool) {
    val ledger = KtSlowLedger()
    val server = Server(pool)
    val connector = ServerConnector(server).apply { host = "127.0.0.1"; port = 0 }
    server.addConnector(connector)
    server.handler = ledger
    server.start()
    val uri = URI.create("http://127.0.0.1:${connector.localPort}/")
    val t0 = System.nanoTime()
    val calls = List(40) { loadClient.sendAsync(HttpRequest.newBuilder(uri).build(), HttpResponse.BodyHandlers.ofString()) }
    calls.forEach { it.get(30, TimeUnit.SECONDS) }
    println("%-38s 40 x 300 ms -> %,5d ms, at most %d in the handler at once".format(label, (System.nanoTime() - t0) / 1_000_000, ledger.max.get()))
    server.stop()
}

fun main() {
    runLoad("QueuedThreadPool(max=12)", QueuedThreadPool(12))
    val withVirtual = QueuedThreadPool(12)
    withVirtual.virtualThreadsExecutor = VirtualThreads.getNamedVirtualThreadsExecutor("jetty-vt-")
    runLoad("QueuedThreadPool(max=12) + virtual", withVirtual)
    runLoad("VirtualThreadPool(maxThreads=8)", VirtualThreadPool(8))
}

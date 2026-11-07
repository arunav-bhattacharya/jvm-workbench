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
import java.net.URI
import java.net.http.HttpClient
import java.net.http.HttpRequest
import java.net.http.HttpResponse

/** What does a default Jetty 12 server start, and which thread runs a blocking vs a non-blocking handler? */
private val client = HttpClient.newBuilder().proxy(HttpClient.Builder.NO_PROXY).build()

private fun where() = Thread.currentThread().let { "${it.name} virtual=${it.isVirtual}" }

private class KtBlocking : Handler.Abstract() {                       // declares BLOCKING
    override fun handle(request: Request, response: Response, callback: Callback): Boolean {
        Content.Sink.write(response, true, where(), callback)
        return true
    }
}

private class KtNonBlocking : Handler.Abstract.NonBlocking() {        // declares NON_BLOCKING
    override fun handle(request: Request, response: Response, callback: Callback): Boolean {
        Content.Sink.write(response, true, where(), callback)
        return true
    }
}

private fun startServer(pool: ThreadPool, handler: Handler): Server = Server(pool).apply {
    addConnector(ServerConnector(this).apply { host = "127.0.0.1"; port = 0 })
    this.handler = handler
    start()
}

private fun get(server: Server): String {
    val port = (server.connectors[0] as ServerConnector).localPort
    return client.send(HttpRequest.newBuilder(URI.create("http://127.0.0.1:$port/")).build(), HttpResponse.BodyHandlers.ofString()).body()
}

fun main() {
    val defaults = QueuedThreadPool()
    var server = startServer(defaults, KtBlocking())
    val c = server.connectors[0] as ServerConnector
    println("cpus=${Runtime.getRuntime().availableProcessors()} acceptors=${c.acceptors} selectors=${c.selectorManager.selectorCount}")
    println("QueuedThreadPool min=${defaults.minThreads} max=${defaults.maxThreads} started=${defaults.threads} leased=${defaults.leasedThreads}")
    println("[platform pool] BLOCKING handler     -> ${get(server)}")
    server.stop()
    server = startServer(QueuedThreadPool(), KtNonBlocking())
    println("[platform pool] NON_BLOCKING handler -> ${get(server)}")
    server.stop()

    for (blocking in listOf(true, false)) {
        val pool = QueuedThreadPool()
        pool.virtualThreadsExecutor = VirtualThreads.getNamedVirtualThreadsExecutor("jetty-vt-")
        server = startServer(pool, if (blocking) KtBlocking() else KtNonBlocking())
        println("[pool + virtual threads] ${if (blocking) "BLOCKING handler     -> " else "NON_BLOCKING handler -> "}${get(server)}")
        server.stop()
    }
}

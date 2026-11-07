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
import java.net.URI
import java.net.http.HttpClient
import java.net.http.HttpRequest
import java.net.http.HttpResponse

/** Which execution-strategy mode ran the handler? Read it from the handler's own stack. */
private val strategyClient = HttpClient.newBuilder().proxy(HttpClient.Builder.NO_PROXY).build()

private fun strategyMode(): String {
    val methods = Thread.currentThread().stackTrace
        .filter { "AdaptiveExecutionStrategy" in it.className || "VirtualThread" in it.className }
        .map { it.className.substringAfterLast('.') + "." + it.methodName }
    val strategy = methods.firstOrNull { "RunTask" in it && it != "AdaptiveExecutionStrategy.runTask" }
        ?: methods.firstOrNull() ?: "no strategy frame: dispatched to the pool"
    return "${Thread.currentThread().name} :: $strategy"
}

private fun modeHandler(nonBlocking: Boolean): Handler =
    if (nonBlocking) object : Handler.Abstract.NonBlocking() {
        override fun handle(request: Request, response: Response, callback: Callback): Boolean {
            Content.Sink.write(response, true, strategyMode(), callback); return true
        }
    } else object : Handler.Abstract() {
        override fun handle(request: Request, response: Response, callback: Callback): Boolean {
            Content.Sink.write(response, true, strategyMode(), callback); return true
        }
    }

fun main() {
    for (setup in listOf("default pool, BLOCKING", "default pool, NON_BLOCKING", "reservedThreads=0, BLOCKING", "virtual threads, BLOCKING")) {
        val pool = QueuedThreadPool()
        if (setup.startsWith("reservedThreads=0")) pool.reservedThreads = 0
        if (setup.startsWith("virtual")) pool.virtualThreadsExecutor = VirtualThreads.getNamedVirtualThreadsExecutor("jetty-vt-")
        val server = Server(pool)
        val connector = ServerConnector(server).apply { host = "127.0.0.1"; port = 0 }
        server.addConnector(connector)
        server.handler = modeHandler(setup.endsWith("NON_BLOCKING"))
        server.start()
        val uri = URI.create("http://127.0.0.1:${connector.localPort}/")
        strategyClient.send(HttpRequest.newBuilder(uri).build(), HttpResponse.BodyHandlers.ofString())   // warm up the connection
        println("%-28s -> %s".format(setup, strategyClient.send(HttpRequest.newBuilder(uri).build(), HttpResponse.BodyHandlers.ofString()).body()))
        server.stop()
    }
}

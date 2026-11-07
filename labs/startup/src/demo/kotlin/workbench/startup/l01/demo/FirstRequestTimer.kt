package workbench.startup.l01.demo

import com.sun.net.httpserver.HttpServer
import java.io.IOException
import java.lang.management.ManagementFactory
import java.net.InetAddress
import java.net.InetSocketAddress
import java.net.ServerSocket
import java.net.URI
import java.net.http.HttpClient
import java.net.http.HttpRequest
import java.net.http.HttpResponse
import java.nio.file.Files
import java.nio.file.Path
import java.time.Duration
import java.util.concurrent.CopyOnWriteArrayList
import kotlin.concurrent.thread

/**
 * Launches a tiny HTTP service in a second JVM and reads three clocks: the JVM's own
 * "Create VM" line (pass -Xlog:startuptime), the service's "started in" line, and the time
 * to the first 200, measured from outside. Then it reads the service's RSS.
 */
fun main(args: Array<String>) {
    if (args.size > 1 && args[0] == "--serve") {
        serve(args[1].toInt())
        return
    }
    val port = ServerSocket(0, 1, InetAddress.getLoopbackAddress()).use { it.localPort }
    val cmd = buildList {
        add(Path.of(System.getProperty("java.home"), "bin", "java").toString())
        addAll(args)                                     // e.g. -Xlog:startuptime, -Xshare:off
        addAll(listOf("-cp", System.getProperty("java.class.path"),
            "workbench.startup.l01.demo.FirstRequestTimerKt", "--serve", port.toString()))
    }

    // 1. warm up our own HTTP client (nothing listens yet), then start the clock and the service
    val client = HttpClient.newBuilder().proxy(HttpClient.Builder.NO_PROXY).build()
    val hello = HttpRequest.newBuilder(URI.create("http://127.0.0.1:$port/hello")).build()
    try {
        client.send(hello, HttpResponse.BodyHandlers.ofString())
    } catch (expected: IOException) {
        // refused: good, the client's own classes are loaded now
    }
    val t0 = System.nanoTime()
    val service = ProcessBuilder(cmd).redirectErrorStream(true).start()
    val serviceLog = CopyOnWriteArrayList<String>()
    thread(isDaemon = true) { service.inputReader().lines().forEach(serviceLog::add) }

    // 2. poll from outside every 2 ms until the first 200
    var attempts = 0
    var firstOk = -1L
    while (firstOk < 0 && System.nanoTime() - t0 < Duration.ofSeconds(8).toNanos()) {
        attempts++
        try {
            if (client.send(hello, HttpResponse.BodyHandlers.ofString()).statusCode() == 200) {
                firstOk = System.nanoTime() - t0
            }
        } catch (notUpYet: IOException) {
            Thread.sleep(2)
        }
    }

    // 3. footprint of the whole process, as the OS sees it, and the JVM's own accounting
    val rss = rss(service.pid())
    val nmt = if (args.any { it.startsWith("-XX:NativeMemoryTracking") }) nmt(service.pid()) else emptyList()
    service.destroy()
    service.waitFor()

    println("JDK ${Runtime.version()}, flags ${args.toList()}")
    serviceLog.filter { "Create VM" in it || "started in" in it }.forEach { println("  log      : $it") }
    println("  first 200: ${firstOk / 1_000_000} ms after launch, measured outside ($attempts attempts)")
    println("  RSS      : $rss")
    nmt.forEach { println("  NMT      : $it") }
}

/** Asks the running service for its Native Memory Tracking summary (needs -XX:NativeMemoryTracking=summary). */
private fun nmt(pid: Long): List<String> {
    val jcmd = Path.of(System.getProperty("java.home"), "bin", "jcmd").toString()
    val p = ProcessBuilder(jcmd, pid.toString(), "VM.native_memory", "summary", "scale=MB")
        .redirectErrorStream(true).start()
    return p.inputReader().useLines { lines ->
        lines.filter { "Total:" in it || "Java Heap (" in it }.map { it.replace("-", "").trim() }.toList()
    }
}

/** RSS from /proc on Linux, from ps elsewhere. Both count the whole process, not just the heap. */
private fun rss(pid: Long): String {
    val status = Path.of("/proc", pid.toString(), "status")
    if (Files.exists(status)) {
        return Files.readAllLines(status)
            .filter { it.startsWith("VmRSS") || it.startsWith("RssAnon") || it.startsWith("RssFile") }
            .joinToString(", ") { it.replace(Regex("\\s+"), " ") }
    }
    val ps = ProcessBuilder("ps", "-o", "rss=", "-p", pid.toString()).start()
    return ps.inputStream.readAllBytes().decodeToString().trim() + " kB (ps)"
}

/** The service: one endpoint, and a Quarkus-style "started in" line, from the JVM's uptime. */
private fun serve(port: Int) {
    val server = HttpServer.create(InetSocketAddress(InetAddress.getLoopbackAddress(), port), 0)
    server.createContext("/hello") { exchange ->
        val body = """{"status":"AUTHORIZED","amountMinor":1250}""".toByteArray()
        exchange.responseHeaders.add("Content-Type", "application/json")
        exchange.sendResponseHeaders(200, body.size.toLong())
        exchange.responseBody.write(body)
        exchange.close()
    }
    server.start()
    val uptimeMs = ManagementFactory.getRuntimeMXBean().uptime           // since the JVM started
    println("started in %.3fs. Listening on: http://127.0.0.1:%d".format(uptimeMs / 1000.0, port))
}

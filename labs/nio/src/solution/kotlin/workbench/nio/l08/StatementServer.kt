package workbench.nio.l08

import java.io.IOException
import java.net.InetAddress
import java.net.InetSocketAddress
import java.nio.channels.Channels
import java.nio.channels.FileChannel
import java.nio.channels.ServerSocketChannel
import java.nio.channels.SocketChannel
import java.nio.file.Path
import java.util.concurrent.Executors
import java.util.concurrent.Semaphore
import java.util.concurrent.atomic.AtomicInteger
import kotlin.concurrent.thread

/**
 * Serves settlement statement files: a client sends a day (`2026-11-06\n`) and gets the bytes of
 * `<day>.csv` from [statements], then the connection closes.
 *
 * One virtual thread per connection (plain blocking code; a blocked read parks on the JDK's poller).
 * Each export first runs a 100 ms "query" (a blocking database call), then sends the file with
 * zero-copy [FileSender.transferFully].
 *
 * A Semaphore keeps the exports at [maxConcurrentExports] at once.
 */
class StatementServer(private val statements: Path, private val maxConcurrentExports: Int) : AutoCloseable {
    private val server = ServerSocketChannel.open().bind(InetSocketAddress(InetAddress.getLoopbackAddress(), 0))
    private val handlers = Executors.newVirtualThreadPerTaskExecutor()
    private val inFlight = AtomicInteger()
    private val maxInFlight = AtomicInteger()
    private val exportSlots = Semaphore(maxConcurrentExports)       // virtual threads are cheap; the database isn't

    val port: Int = (server.localAddress as InetSocketAddress).port

    /** The most exports that were running at the same time. */
    fun maxConcurrent(): Int = maxInFlight.get()

    init {
        thread(isDaemon = true, name = "statement-acceptor") {
            while (server.isOpen) {
                val ch = try {
                    server.accept()
                } catch (e: IOException) {
                    break                                      // closed
                }
                handlers.execute { serve(ch) }                 // one virtual thread per connection
            }
        }
    }

    private fun serve(ch: SocketChannel) {
        ch.use {
            val day = Channels.newInputStream(ch).bufferedReader().readLine() ?: return   // parks the virtual thread
            export(day.trim(), ch)
        }
    }

    /** Counts exports in progress; wrap the work of one export in it. */
    private fun <T> measured(work: () -> T): T {
        maxInFlight.accumulateAndGet(inFlight.incrementAndGet()) { a, b -> maxOf(a, b) }
        try {
            return work()
        } finally {
            inFlight.decrementAndGet()
        }
    }

    fun export(day: String, out: SocketChannel) {
        exportSlots.acquire()                                  // waiting here parks the virtual thread, no carrier held
        try {
            measured {
                Thread.sleep(QUERY_MILLIS)                     // the statement query: blocks, parks the virtual thread
                FileChannel.open(statements.resolve("$day.csv")).use { file ->
                    FileSender.transferFully(file, 0, file.size(), out)   // sendfile on Linux
                }
            }
        } finally {
            exportSlots.release()
        }
    }

    override fun close() {
        server.close()
        handlers.shutdownNow()
    }

    companion object {
        const val QUERY_MILLIS = 100L
    }
}

package workbench.nio.l08

import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.Timeout
import org.junit.jupiter.api.io.TempDir
import java.io.ByteArrayOutputStream
import java.lang.management.ManagementFactory
import java.net.InetAddress
import java.net.Socket
import java.nio.ByteBuffer
import java.nio.channels.FileChannel
import java.nio.channels.WritableByteChannel
import java.nio.file.Files
import java.nio.file.Path
import java.util.concurrent.Callable
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import kotlin.random.Random

@Timeout(30)
class StatementServerTest {
    @TempDir
    lateinit var dir: Path

    /** A channel that takes at most 4 KiB per write, like a socket whose buffer is nearly full. */
    private class TrickleChannel : WritableByteChannel {
        val received = ByteArrayOutputStream()
        override fun write(src: ByteBuffer): Int {
            val n = minOf(src.remaining(), 4 * 1024)
            val bytes = ByteArray(n)
            src.get(bytes)
            received.write(bytes)
            return n
        }
        override fun isOpen() = true
        override fun close() {}
    }

    private fun statement(day: String, size: Int): ByteArray {
        val bytes = Random(day.hashCode()).nextBytes(size)
        Files.write(dir.resolve("$day.csv"), bytes)
        return bytes
    }

    private fun download(port: Int, day: String): ByteArray =
        Socket(InetAddress.getLoopbackAddress(), port).use { s ->
            s.soTimeout = 10_000
            s.getOutputStream().write("$day\n".toByteArray())
            s.getInputStream().readAllBytes()                 // the server closes after the last byte
        }

    @Test
    fun `transferFully keeps calling transferTo until every byte is sent`() {
        val expected = statement("2026-11-01", 1024 * 1024)
        val target = TrickleChannel()
        val calls = FileChannel.open(dir.resolve("2026-11-01.csv")).use { f ->
            FileSender.transferFully(f, 0, f.size(), target)
        }
        assertThat(target.received.toByteArray()).isEqualTo(expected)
        assertThat(calls).`as`("transferTo calls for 1 MiB at 4 KiB per write").isGreaterThanOrEqualTo(256)
    }

    @Test
    fun `twenty concurrent downloads get every byte, with at most four exports at once`() {
        val expected = statement("2026-11-06", 512 * 1024)
        StatementServer(dir, maxConcurrentExports = 4).use { server ->
            val clients = Executors.newFixedThreadPool(20)
            try {
                val downloads = List(20) { clients.submit(Callable { download(server.port, "2026-11-06") }) }
                for (d in downloads) assertThat(d.get(20, TimeUnit.SECONDS)).isEqualTo(expected)
            } finally {
                clients.shutdownNow()
            }
            assertThat(server.maxConcurrent()).`as`("exports running at once").isBetween(1, 4)
        }
    }

    @Test
    fun `300 idle connections cost a handful of platform threads`() {
        StatementServer(dir, maxConcurrentExports = 4).use { server ->
            val before = ManagementFactory.getThreadMXBean().threadCount   // platform threads only
            val idle = List(300) { Socket(InetAddress.getLoopbackAddress(), server.port) }
            try {
                Thread.sleep(300)                                          // every handler is now parked in readLine()
                val after = ManagementFactory.getThreadMXBean().threadCount
                assertThat(after - before).`as`("new platform threads for 300 parked handlers").isLessThan(40)
            } finally {
                idle.forEach { it.close() }
            }
        }
    }
}

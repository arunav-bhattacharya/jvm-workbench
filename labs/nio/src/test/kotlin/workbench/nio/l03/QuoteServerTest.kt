package workbench.nio.l03

import io.netty.buffer.ByteBuf
import io.netty.buffer.Unpooled
import io.netty.channel.MultiThreadIoEventLoopGroup
import io.netty.channel.embedded.EmbeddedChannel
import io.netty.handler.codec.TooLongFrameException
import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.Timeout
import java.io.BufferedReader
import java.net.InetAddress
import java.net.Socket
import java.util.concurrent.Callable
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import kotlin.text.Charsets.UTF_8

@Timeout(20)
class QuoteServerTest {

    private fun EmbeddedChannel.drainOutbound(): List<String> = buildList {
        while (true) {
            val buf = readOutbound<ByteBuf>() ?: break
            add(buf.toString(UTF_8))
            buf.release()                       // the test owns what it reads
        }
    }

    @Test
    fun `the pipeline frames lines that arrive in fragments`() {
        val ch = EmbeddedChannel(*QuotePipeline.handlers(UpperCaseHandler()))
        ch.writeInbound(Unpooled.copiedBuffer("hel", UTF_8))
        assertThat(ch.drainOutbound()).isEmpty()
        ch.writeInbound(Unpooled.copiedBuffer("lo\nwor", UTF_8))
        assertThat(ch.drainOutbound()).containsExactly("HELLO\n")
        ch.writeInbound(Unpooled.copiedBuffer("ld\n", UTF_8))
        assertThat(ch.drainOutbound()).containsExactly("WORLD\n")
        assertThat(ch.finish()).`as`("nothing left over").isFalse()
    }

    @Test
    fun `a line longer than 64 bytes is rejected`() {
        val ch = EmbeddedChannel(*QuotePipeline.handlers(UpperCaseHandler()))
        assertThatThrownBy { ch.writeInbound(Unpooled.copiedBuffer("x".repeat(100) + "\n", UTF_8)) }
            .isInstanceOf(TooLongFrameException::class.java)
            .hasMessage("frame length (100) exceeds the allowed maximum (64)")
        ch.finishAndReleaseAll()
    }

    private class Client(port: Int) : AutoCloseable {
        val socket = Socket(InetAddress.getLoopbackAddress(), port).apply { soTimeout = 5_000 }
        val reader: BufferedReader = socket.getInputStream().bufferedReader(UTF_8)
        fun send(line: String) = socket.getOutputStream().run { write("$line\n".toByteArray(UTF_8)); flush() }
        override fun close() = socket.close()
    }

    @Test
    fun `the server answers over TCP on a Netty 4_2 event loop group`() {
        val pool = Executors.newFixedThreadPool(2)
        QuoteServer(pool) { "quote $it" }.use { server ->
            assertThat(server.group).isInstanceOf(MultiThreadIoEventLoopGroup::class.java)
            Client(server.port()).use { c ->
                c.send("EURUSD")
                assertThat(c.reader.readLine()).isEqualTo("quote EURUSD")
            }
        }
        pool.shutdown()
    }

    @Test
    fun `a slow lookup runs on the blocking pool and does not stall the event loop`() {
        val pool = Executors.newFixedThreadPool(4) { r -> Thread(r, "quote-blocking") }
        val lookupThreads = ConcurrentHashMap.newKeySet<String>()
        val lookup: (String) -> String = { key ->
            lookupThreads += Thread.currentThread().name
            if (key == "SLOW") Thread.sleep(1_000)          // stands in for a 1 s JDBC call
            "quote $key"
        }
        QuoteServer(pool, lookup).use { server ->
            Client(server.port()).use { slow ->
                Client(server.port()).use { fast ->
                    slow.send("SLOW")
                    Thread.sleep(100)                        // the slow lookup is now running somewhere

                    // lag probe: how long does a trivial task wait to run on the event loop?
                    val t0 = System.nanoTime()
                    val lagMs = server.group.next().submit(Callable { (System.nanoTime() - t0) / 1_000_000 }).get(5, TimeUnit.SECONDS)
                    assertThat(lagMs).`as`("event loop lag while SLOW runs, ms").isLessThan(300)

                    val f0 = System.nanoTime()
                    fast.send("FAST")
                    assertThat(fast.reader.readLine()).isEqualTo("quote FAST")
                    assertThat((System.nanoTime() - f0) / 1_000_000).`as`("FAST round trip, ms").isLessThan(300)

                    assertThat(slow.reader.readLine()).isEqualTo("quote SLOW")
                }
            }
        }
        pool.shutdown()
        assertThat(lookupThreads).`as`("threads that ran the lookup").containsOnly("quote-blocking")
    }
}

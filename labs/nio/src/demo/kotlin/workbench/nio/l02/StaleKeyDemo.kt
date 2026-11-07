package workbench.nio.l02

import java.net.InetAddress
import java.net.InetSocketAddress
import java.nio.ByteBuffer
import java.nio.channels.SelectionKey
import java.nio.channels.Selector
import java.nio.channels.ServerSocketChannel
import java.nio.channels.SocketChannel

/** One message arrives. How many times does the loop think the channel is readable? */
fun main() {
    staleKeys(removeHandledKeys = true)
    staleKeys(removeHandledKeys = false)
}

private fun staleKeys(removeHandledKeys: Boolean) {
    Selector.open().use { selector ->
        ServerSocketChannel.open().use { server ->
            server.bind(InetSocketAddress(InetAddress.getLoopbackAddress(), 0))
            SocketChannel.open(server.localAddress).use { client ->
                server.accept().use { conn ->
                    conn.configureBlocking(false)
                    conn.register(selector, SelectionKey.OP_READ)
                    client.write(ByteBuffer.wrap("auth-1".toByteArray()))   // exactly one message

                    val buf = ByteBuffer.allocate(64)
                    var loops = 0
                    var handled = 0
                    var bytes = 0
                    val end = System.nanoTime() + 300_000_000L
                    while (System.nanoTime() < end) {
                        selector.select(50)
                        loops++
                        val it = selector.selectedKeys().iterator()
                        while (it.hasNext()) {
                            val key = it.next()
                            if (removeHandledKeys) it.remove()
                            if (key.isReadable) {               // ready set from the last select that added the key
                                handled++
                                buf.clear()
                                bytes += maxOf(0, conn.read(buf))
                            }
                        }
                    }
                    println("remove handled keys=%-5s loops=%d, handled as readable %d times, bytes read %d"
                        .format(removeHandledKeys, loops, handled, bytes))
                }
            }
        }
    }
}

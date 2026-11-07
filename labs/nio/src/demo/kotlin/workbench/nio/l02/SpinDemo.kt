package workbench.nio.l02

import java.net.InetAddress
import java.net.InetSocketAddress
import java.nio.channels.SelectionKey
import java.nio.channels.Selector
import java.nio.channels.ServerSocketChannel
import java.nio.channels.SocketChannel

/** Counts how often select() wakes up on one idle connection, with and without OP_WRITE in the interest set. */
fun main() {
    Selector.open().use { println("Selector implementation: ${it.javaClass.name}") }
    println("idle 300 ms, interest OP_READ           : ${idleWakeups(SelectionKey.OP_READ)} wakeups")
    println("idle 300 ms, interest OP_READ | OP_WRITE: ${idleWakeups(SelectionKey.OP_READ or SelectionKey.OP_WRITE)} wakeups")
}

private fun idleWakeups(interest: Int): Long =
    Selector.open().use { selector ->
        ServerSocketChannel.open().use { server ->
            server.bind(InetSocketAddress(InetAddress.getLoopbackAddress(), 0))
            SocketChannel.open(server.localAddress).use { _ ->
                server.accept().use { conn ->
                    conn.configureBlocking(false)
                    conn.register(selector, interest)
                    val end = System.nanoTime() + 300_000_000L
                    var count = 0L
                    while (System.nanoTime() < end) {
                        if (selector.select(50) > 0) count++   // nobody sends anything on this connection
                        selector.selectedKeys().clear()
                    }
                    count
                }
            }
        }
    }

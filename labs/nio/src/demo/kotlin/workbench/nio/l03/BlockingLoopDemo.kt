package workbench.nio.l03

import io.netty.bootstrap.ServerBootstrap
import io.netty.channel.ChannelHandlerContext
import io.netty.channel.ChannelInitializer
import io.netty.channel.MultiThreadIoEventLoopGroup
import io.netty.channel.SimpleChannelInboundHandler
import io.netty.channel.nio.NioIoHandler
import io.netty.channel.socket.SocketChannel
import io.netty.channel.socket.nio.NioServerSocketChannel
import io.netty.handler.codec.LineBasedFrameDecoder
import io.netty.handler.codec.string.StringDecoder
import io.netty.handler.codec.string.StringEncoder
import java.net.InetAddress
import java.net.InetSocketAddress
import java.net.Socket
import java.util.concurrent.Callable
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import kotlin.text.Charsets.UTF_8

/** One event loop. Client A asks for SLOW (a 1 s "JDBC call"); client B asks for FAST 50 ms later. */
fun main() {
    runLoop(dispatch = false)
    runLoop(dispatch = true)
}

private fun slowWork(line: String): String {
    if (line == "SLOW") Thread.sleep(1_000)   // stands in for a blocking JDBC call
    return "$line on ${Thread.currentThread().name}"
}

private fun runLoop(dispatch: Boolean) {
    val group = MultiThreadIoEventLoopGroup(1, NioIoHandler.newFactory())
    val blockingPool = Executors.newFixedThreadPool(4) { r -> Thread(r, "app-blocking-pool") }
    try {
        val server = ServerBootstrap().group(group).channel(NioServerSocketChannel::class.java)
            .childHandler(object : ChannelInitializer<SocketChannel>() {
                override fun initChannel(ch: SocketChannel) {
                    ch.pipeline().addLast(LineBasedFrameDecoder(1024), StringDecoder(UTF_8), StringEncoder(UTF_8),
                        object : SimpleChannelInboundHandler<String>() {
                            override fun channelRead0(ctx: ChannelHandlerContext, line: String) {
                                if (!dispatch) {
                                    ctx.writeAndFlush(slowWork(line) + "\n")      // blocks the event loop
                                    return
                                }
                                blockingPool.execute {                            // leave the loop for the slow part
                                    ctx.writeAndFlush(slowWork(line) + "\n")     // safe from any thread
                                }
                            }
                        })
                }
            })
            .bind(InetAddress.getLoopbackAddress(), 0).sync().channel()
        val port = (server.localAddress() as InetSocketAddress).port
        Socket(InetAddress.getLoopbackAddress(), port).use { a ->
            Socket(InetAddress.getLoopbackAddress(), port).use { b ->
                val aIn = a.getInputStream().bufferedReader(UTF_8)
                val bIn = b.getInputStream().bufferedReader(UTF_8)
                a.getOutputStream().write("SLOW\n".toByteArray(UTF_8))
                Thread.sleep(50)

                val t0 = System.nanoTime()
                b.getOutputStream().write("FAST\n".toByteArray(UTF_8))
                // lag probe: how long until a trivial task runs on the loop?
                val lagMs = group.next().submit(Callable { (System.nanoTime() - t0) / 1_000_000 }).get(5, TimeUnit.SECONDS)
                val fast = bIn.readLine()
                val fastMs = (System.nanoTime() - t0) / 1_000_000

                println(if (dispatch) "[dispatch to app pool]" else "[blocking in the handler]")
                println("   event-loop lag probe: $lagMs ms")
                println("   FAST reply after $fastMs ms: $fast")
                println("   SLOW reply: ${aIn.readLine()}")
            }
        }
        server.close().sync()
    } finally {
        group.shutdownGracefully(0, 1, TimeUnit.SECONDS).sync()   // close channels and loops first...
        blockingPool.shutdown()                                     // ...then the pool they write from
    }
}

package workbench.nio.l04

import io.netty.bootstrap.ServerBootstrap
import io.netty.channel.ChannelHandlerContext
import io.netty.channel.ChannelInboundHandlerAdapter
import io.netty.channel.ChannelInitializer
import io.netty.channel.ChannelOption
import io.netty.channel.MultiThreadIoEventLoopGroup
import io.netty.channel.nio.NioIoHandler
import io.netty.channel.socket.SocketChannel
import io.netty.channel.socket.nio.NioServerSocketChannel
import java.io.IOException
import java.net.InetAddress
import java.net.Socket
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicLong
import kotlin.concurrent.thread

/**
 * An echo server and a client that writes 8 MiB fast but reads slowly. How much piles up in the
 * server's outbound buffer, with and without backpressure?
 */
fun main() {
    for (backpressure in listOf(false, true)) {
        println("backpressure=%-5s -> peak bytes waiting in the outbound buffer: %,d".format(backpressure, peakPending(backpressure, 8)))
    }
}

private fun peakPending(backpressure: Boolean, megabytes: Int): Long {
    val group = MultiThreadIoEventLoopGroup(1, NioIoHandler.newFactory())
    val peak = AtomicLong()
    try {
        val server = ServerBootstrap().group(group).channel(NioServerSocketChannel::class.java)
            .childOption(ChannelOption.SO_SNDBUF, 32 * 1024)
            .childOption(ChannelOption.SO_RCVBUF, 32 * 1024)
            .childHandler(object : ChannelInitializer<SocketChannel>() {
                override fun initChannel(ch: SocketChannel) {
                    ch.pipeline().addLast(object : ChannelInboundHandlerAdapter() {
                        override fun channelRead(ctx: ChannelHandlerContext, msg: Any) {
                            ctx.write(msg)   // queue the echo in the outbound buffer
                            val pending = ctx.channel().unsafe().outboundBuffer().totalPendingWriteBytes()
                            peak.accumulateAndGet(pending) { a, b -> maxOf(a, b) }
                        }

                        override fun channelReadComplete(ctx: ChannelHandlerContext) {
                            ctx.flush()
                            if (backpressure && !ctx.channel().isWritable) {
                                ctx.channel().config().isAutoRead = false   // stop reading from a peer we can't write to
                            }
                        }

                        override fun channelWritabilityChanged(ctx: ChannelHandlerContext) {
                            if (backpressure && ctx.channel().isWritable) {
                                ctx.channel().config().isAutoRead = true    // drained below the low water mark
                            }
                            ctx.fireChannelWritabilityChanged()
                        }
                    })
                }
            })
            .bind(InetAddress.getLoopbackAddress(), 0).sync().channel()

        val total = megabytes shl 20
        Socket().use { s ->
            s.receiveBufferSize = 32 * 1024
            s.sendBufferSize = 32 * 1024
            s.connect(server.localAddress())
            val writer = thread {                                  // the fast writer
                try {
                    val out = s.getOutputStream()
                    val chunk = ByteArray(64 * 1024)
                    repeat(total / chunk.size) { out.write(chunk) }
                    s.shutdownOutput()
                } catch (_: IOException) {
                }
            }
            val input = s.getInputStream()                         // the slow reader: 20 ms pause per 128 KiB
            val buf = ByteArray(16 * 1024)
            var got = 0L
            while (got < total) {
                val n = input.read(buf)
                if (n < 0) break
                got += n
                if ((got and ((128L shl 10) - 1)) < n) Thread.sleep(20)
            }
            writer.join()
        }
        server.close().sync()
    } finally {
        group.shutdownGracefully(0, 1, TimeUnit.SECONDS).sync()
    }
    return peak.get()
}

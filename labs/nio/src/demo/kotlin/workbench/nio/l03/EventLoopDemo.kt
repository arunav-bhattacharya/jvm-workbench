package workbench.nio.l03

import io.netty.bootstrap.ServerBootstrap
import io.netty.channel.ChannelHandlerContext
import io.netty.channel.ChannelInboundHandlerAdapter
import io.netty.channel.ChannelInitializer
import io.netty.channel.MultiThreadIoEventLoopGroup
import io.netty.channel.nio.NioIoHandler
import io.netty.channel.socket.SocketChannel
import io.netty.channel.socket.nio.NioServerSocketChannel
import java.net.InetAddress
import java.net.InetSocketAddress
import java.net.Socket
import java.util.concurrent.TimeUnit

/** Which event-loop thread serves each connection? One acceptor loop, two worker loops, four clients. */
fun main() {
    val defaults = MultiThreadIoEventLoopGroup(NioIoHandler.newFactory())
    println("default loop count: ${defaults.executorCount()} (availableProcessors=${Runtime.getRuntime().availableProcessors()})")
    defaults.shutdownGracefully(0, 0, TimeUnit.SECONDS).sync()

    val boss = MultiThreadIoEventLoopGroup(1, NioIoHandler.newFactory())      // accepts
    val workers = MultiThreadIoEventLoopGroup(2, NioIoHandler.newFactory())   // serves
    try {
        val server = ServerBootstrap()
            .group(boss, workers)
            .channel(NioServerSocketChannel::class.java)
            .childHandler(object : ChannelInitializer<SocketChannel>() {
                override fun initChannel(ch: SocketChannel) {
                    ch.pipeline().addLast(object : ChannelInboundHandlerAdapter() {
                        override fun channelActive(ctx: ChannelHandlerContext) {
                            val port = (ctx.channel().remoteAddress() as InetSocketAddress).port
                            println("client port $port registered on ${Thread.currentThread().name}, inEventLoop=${ctx.channel().eventLoop().inEventLoop()}")
                        }

                        override fun channelRead(ctx: ChannelHandlerContext, msg: Any) {
                            val port = (ctx.channel().remoteAddress() as InetSocketAddress).port
                            println("   bytes from port $port handled on ${Thread.currentThread().name}")
                            ctx.writeAndFlush(msg)   // echo: the write takes ownership of msg, no release here
                        }
                    })
                }
            })
            .bind(InetAddress.getLoopbackAddress(), 0).sync().channel()
        val port = (server.localAddress() as InetSocketAddress).port

        repeat(4) {
            Socket(InetAddress.getLoopbackAddress(), port).use { client ->
                client.getOutputStream().write("hi".toByteArray())
                client.getInputStream().readNBytes(2)
            }
        }
        server.close().sync()
    } finally {
        boss.shutdownGracefully(0, 1, TimeUnit.SECONDS).sync()
        workers.shutdownGracefully(0, 1, TimeUnit.SECONDS).sync()
    }
}

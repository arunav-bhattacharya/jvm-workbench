package workbench.nio.l08

import io.netty.bootstrap.ServerBootstrap
import io.netty.channel.ChannelFutureListener
import io.netty.channel.ChannelHandlerContext
import io.netty.channel.ChannelInboundHandlerAdapter
import io.netty.channel.DefaultFileRegion
import io.netty.channel.IoHandlerFactory
import io.netty.channel.MultiThreadIoEventLoopGroup
import io.netty.channel.ServerChannel
import io.netty.channel.epoll.Epoll
import io.netty.channel.epoll.EpollIoHandler
import io.netty.channel.epoll.EpollServerSocketChannel
import io.netty.channel.kqueue.KQueue
import io.netty.channel.kqueue.KQueueIoHandler
import io.netty.channel.kqueue.KQueueServerSocketChannel
import io.netty.channel.nio.NioIoHandler
import io.netty.channel.socket.nio.NioServerSocketChannel
import io.netty.channel.uring.IoUring
import io.netty.channel.uring.IoUringIoHandler
import io.netty.channel.uring.IoUringServerSocketChannel
import java.io.RandomAccessFile
import java.net.InetAddress
import java.net.InetSocketAddress
import java.net.Socket
import java.nio.file.Files
import java.nio.file.Path
import java.util.concurrent.TimeUnit

/** Sends a 32 MiB file with Netty's DefaultFileRegion over every transport available on this machine. */
fun main() {
    val size = 32L shl 20
    val file = Files.createTempFile("statement", ".bin")
    RandomAccessFile(file.toFile(), "rw").use { it.setLength(size) }
    try {
        sendRegion("nio", NioIoHandler.newFactory(), NioServerSocketChannel::class.java, file, size)
        if (Epoll.isAvailable()) sendRegion("epoll", EpollIoHandler.newFactory(), EpollServerSocketChannel::class.java, file, size)
        else println("epoll    unavailable: ${Epoll.unavailabilityCause()}")
        if (KQueue.isAvailable()) sendRegion("kqueue", KQueueIoHandler.newFactory(), KQueueServerSocketChannel::class.java, file, size)
        else println("kqueue   unavailable: ${KQueue.unavailabilityCause()}")
        if (IoUring.isAvailable()) sendRegion("io_uring", IoUringIoHandler.newFactory(), IoUringServerSocketChannel::class.java, file, size)
        else println("io_uring unavailable: ${IoUring.unavailabilityCause()}")
    } finally {
        Files.delete(file)
    }
}

private fun sendRegion(name: String, factory: IoHandlerFactory, channelClass: Class<out ServerChannel>, file: Path, size: Long) {
    val group = MultiThreadIoEventLoopGroup(1, factory)              // same group type, different IoHandler
    try {
        val server = ServerBootstrap().group(group).channel(channelClass)
            .childHandler(object : ChannelInboundHandlerAdapter() {
                override fun channelActive(ctx: ChannelHandlerContext) {
                    ctx.writeAndFlush(DefaultFileRegion(file.toFile(), 0, size))   // zero-copy where the transport can
                        .addListener(ChannelFutureListener.CLOSE)
                }
            })
            .bind(InetAddress.getLoopbackAddress(), 0).sync().channel()
        val t0 = System.nanoTime()
        var received = 0L
        Socket(InetAddress.getLoopbackAddress(), (server.localAddress() as InetSocketAddress).port).use { s ->
            val input = s.getInputStream()
            val buf = ByteArray(1 shl 16)
            while (true) {
                val r = input.read(buf)
                if (r < 0) break
                received += r
            }
        }
        println("%-8s received %,d bytes in %d ms".format(name, received, (System.nanoTime() - t0) / 1_000_000))
        server.close().sync()
    } finally {
        group.shutdownGracefully(0, 0, TimeUnit.SECONDS).sync()
    }
}

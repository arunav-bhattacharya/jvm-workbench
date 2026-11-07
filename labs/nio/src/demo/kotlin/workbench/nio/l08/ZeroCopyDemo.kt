package workbench.nio.l08

import java.io.IOException
import java.io.RandomAccessFile
import java.net.InetAddress
import java.net.InetSocketAddress
import java.nio.ByteBuffer
import java.nio.channels.FileChannel
import java.nio.channels.ServerSocketChannel
import java.nio.channels.SocketChannel
import java.nio.file.Files
import java.nio.file.Path
import kotlin.concurrent.thread

/** Sends a file over a loopback socket twice: FileChannel.transferTo (zero-copy) and read/write through a heap buffer. Arg: MiB (default 64). */
fun main(args: Array<String>) {
    val size = (args.getOrNull(0)?.toLong() ?: 64L) shl 20
    val file = Files.createTempFile("statement", ".bin")
    RandomAccessFile(file.toFile(), "rw").use { it.setLength(size) }
    try {
        for (mode in listOf("transferTo", "copy")) sendFile(file, size, mode)
    } finally {
        Files.delete(file)
    }
}

private fun sendFile(file: Path, size: Long, mode: String) {
    ServerSocketChannel.open().bind(InetSocketAddress(InetAddress.getLoopbackAddress(), 0)).use { listener ->
        val receiver = thread {                                      // drains the socket, counts bytes
            try {
                listener.accept().use { input ->
                    val b = ByteBuffer.allocateDirect(1 shl 20)
                    while (input.read(b) >= 0) b.clear()
                }
            } catch (e: IOException) {
                e.printStackTrace()
            }
        }
        val t0 = System.nanoTime()
        var calls = 0
        FileChannel.open(file).use { f ->
            SocketChannel.open(listener.localAddress).use { out ->
                if (mode == "transferTo") {
                    var sent = 0L
                    while (sent < size) {                            // may move less than asked: loop
                        sent += f.transferTo(sent, size - sent, out)
                        calls++
                    }
                } else {
                    val b = ByteBuffer.allocate(64 * 1024)           // heap: the JDK copies it again, via a direct buffer
                    while (f.read(b) >= 0) {
                        b.flip()
                        while (b.hasRemaining()) out.write(b)
                        b.clear()
                        calls++
                    }
                }
            }
        }
        receiver.join()
        println("%-10s %d MiB in %4d ms, %,d %s calls".format(mode, size shr 20, (System.nanoTime() - t0) / 1_000_000,
            calls, if (mode == "copy") "read" else "transferTo"))
    }
}

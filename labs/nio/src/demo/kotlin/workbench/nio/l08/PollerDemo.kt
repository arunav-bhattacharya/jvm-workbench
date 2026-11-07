package workbench.nio.l08

import java.io.IOException
import java.net.InetAddress
import java.net.ServerSocket
import java.net.Socket
import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors

/**
 * N virtual threads each block in Socket.read(). Which platform threads exist meanwhile?
 * Args: [N, default 2000] [seconds to hold before releasing them, default 0]
 */
fun main(args: Array<String>) {
    val n = args.getOrNull(0)?.toInt() ?: 2_000
    val holdSeconds = args.getOrNull(1)?.toInt() ?: 0
    println("java ${System.getProperty("java.version")}, cpus=${Runtime.getRuntime().availableProcessors()}, pid=${ProcessHandle.current().pid()}")
    ServerSocket(0, n, InetAddress.getLoopbackAddress()).use { server ->
        Executors.newVirtualThreadPerTaskExecutor().use { readers ->
            val connected = CountDownLatch(n)
            val done = CountDownLatch(n)
            repeat(n) {
                readers.submit {
                    try {
                        Socket(InetAddress.getLoopbackAddress(), server.localPort).use { s ->
                            connected.countDown()
                            s.getInputStream().read()                 // parks this virtual thread on the JDK poller
                        }
                    } catch (e: IOException) {
                        e.printStackTrace()
                    } finally {
                        done.countDown()
                    }
                }
            }
            val accepted = List(n) { server.accept() }
            connected.await()
            Thread.sleep(300)                                         // let every reader reach read()

            val platform = Thread.getAllStackTraces().keys            // platform threads only
                .groupingBy { it.name.replace(Regex("\\d+"), "N") }.eachCount().toSortedMap()
            println("$n virtual threads blocked in read(); platform threads: ${platform.values.sum()}")
            platform.forEach { (name, count) -> println("   $count x $name") }
            if (holdSeconds > 0) {
                println("holding $holdSeconds s: try jcmd ${ProcessHandle.current().pid()} Thread.dump_to_file -format=json dump.json")
                Thread.sleep(holdSeconds * 1_000L)
            }

            val t0 = System.nanoTime()
            accepted.forEach { it.getOutputStream().write(1) }       // data arrives: the poller unparks each reader
            done.await()
            println("wrote 1 byte to each socket: all %,d readers woke and finished in %d ms".format(n, (System.nanoTime() - t0) / 1_000_000))
            accepted.forEach { it.close() }
        }
    }
}

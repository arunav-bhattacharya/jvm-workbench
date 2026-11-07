package workbench.concurrency.scratch

import java.util.concurrent.CompletableFuture
import java.util.concurrent.CompletionException
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.LongAdder
import kotlin.concurrent.thread

class S09Directory { fun lookup(bin: String): String { Thread.sleep(20); return "Northwind Bank" } }

class S09Maps(private val directory: S09Directory) {
    val settledCents = ConcurrentHashMap<String, Long>()
    private val issuers = ConcurrentHashMap<String, String>()

    fun onSettled(merchant: String, cents: Long) {
        settledCents.merge(merchant, cents, Long::plus)     // insert or add, atomically for this key
    }

    fun issuerFor(bin: String): String =
        issuers.computeIfAbsent(bin, directory::lookup)       // lookup runs at most once per BIN

    // compare
    fun issuerForGetOrPut(bin: String): String =
        issuers.getOrPut(bin) { directory.lookup(bin) }           // atomic put, but lookup may run twice

    fun issuerForOnce(bin: String): String =
        issuers.computeIfAbsent(bin) { directory.lookup(it) }     // lookup runs at most once per BIN
}

class S09Memo(private val directory: S09Directory, private val ioPool: ExecutorService) {
    private val issuers = ConcurrentHashMap<String, CompletableFuture<String>>()

    fun issuerFor(bin: String): String {
        // 1. claim the BIN: the function only creates a future, so the bin is locked for microseconds
        val f = issuers.computeIfAbsent(bin) { b ->
            CompletableFuture.supplyAsync({ directory.lookup(b) }, ioPool)
        }
        try {
            return f.join()                                   // 2. wait outside the map, with every other caller
        } catch (e: CompletionException) {
            issuers.remove(bin, f)                            // 3. failed: forget THIS future so a retry loads again
            throw e
        }
    }
}

class S09DeclineCounter {
    private val byReason = ConcurrentHashMap<String, LongAdder>()

    fun record(reason: String) {
        byReason.computeIfAbsent(reason) { LongAdder() }.increment()
    }

    fun count(reason: String): Long = byReason[reason]?.sum() ?: 0L
}

// check the getOrPut claim: with racing threads the default can run more than once
fun main() {
    repeat(3) {
        val calls = AtomicInteger()
        val map = ConcurrentHashMap<String, String>()
        val ts = List(8) { thread { map.getOrPut("411111") { calls.incrementAndGet(); Thread.sleep(50); "Northwind" } } }
        ts.forEach { it.join() }
        val calls2 = AtomicInteger()
        val map2 = ConcurrentHashMap<String, String>()
        val ts2 = List(8) { thread { map2.computeIfAbsent("411111") { calls2.incrementAndGet(); Thread.sleep(50); "Northwind" } } }
        ts2.forEach { it.join() }
        println("getOrPut default ran ${calls.get()} times; computeIfAbsent ran ${calls2.get()} times")
    }
    val pool = Executors.newFixedThreadPool(2)
    println(S09Memo(S09Directory(), pool).issuerFor("411111"))
    pool.shutdown()
}

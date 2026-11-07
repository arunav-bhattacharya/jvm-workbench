package workbench.coroutines.l10

import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext
import java.util.concurrent.atomic.AtomicLong
import kotlin.system.measureTimeMillis

private var plain = 0L
@Volatile private var volatileCount = 0L

/** 100 coroutines on Dispatchers.Default each count 10,000 captured payments. */
suspend fun count(label: String, increment: suspend CoroutineScope.() -> Unit, read: () -> Long) {
    val ms = measureTimeMillis {
        coroutineScope { repeat(100) { launch(Dispatchers.Default) { repeat(10_000) { increment() } } } }
    }
    println("%-28s %,9d of 1,000,000 in %4d ms".format(label, read(), ms))
}

fun main() = runBlocking {
    count("plain var", { plain++ }, { plain })
    count("@Volatile var", { volatileCount++ }, { volatileCount })
    val atomic = AtomicLong()
    count("AtomicLong", { atomic.incrementAndGet() }, { atomic.get() })
    val mutex = Mutex()
    var guarded = 0L
    count("Mutex.withLock", { mutex.withLock { guarded++ } }, { guarded })
    val confined = Dispatchers.Default.limitedParallelism(1)
    var onOneThread = 0L
    count("withContext(limited(1))", { withContext(confined) { onOneThread++ } }, { onOneThread })
}

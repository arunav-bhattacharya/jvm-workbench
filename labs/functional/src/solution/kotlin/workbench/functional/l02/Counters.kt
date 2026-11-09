package workbench.functional.l02

import java.util.concurrent.atomic.AtomicLong

// The captured var becomes a Ref.IntRef box. Fine for one thread: each counter gets its own box.
fun makeCounter(): () -> Int {
    var count = 0
    return { ++count }
}

// Capture a val that holds a thread-safe object instead of a var. incrementAndGet is one atomic step.
fun makeSharedCounter(): () -> Long {
    val count = AtomicLong()
    return { count.incrementAndGet() }
}

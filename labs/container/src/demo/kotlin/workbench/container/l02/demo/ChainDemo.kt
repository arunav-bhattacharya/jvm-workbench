package workbench.container.l02.demo

import workbench.container.l02.CallLog
import workbench.container.l02.Interceptor
import workbench.container.l02.Invocation
import workbench.container.l02.RetryInterceptor
import workbench.container.l02.TimedInterceptor
import java.util.concurrent.atomic.AtomicLong
import java.util.function.LongSupplier

// One issuer call that fails twice, sent through the same two interceptors in both orders.
fun main() {
    val ticks = AtomicLong()
    val clock = LongSupplier { ticks.addAndGet(10_000_000) }          // a fake clock: 10 ms per read
    val shout = Interceptor { inv ->                                  // a third interceptor, to watch proceed()
        println("    -> ${inv.name}")
        try { inv.proceed() } finally { println("    <- ${inv.name}") }
    }

    for (order in listOf("timed, retry", "retry, timed")) {
        val log = CallLog()
        val timed = TimedInterceptor(log, clock)
        val retry = RetryInterceptor(3, listOf(IllegalStateException::class.java))
        val chain = if (order.startsWith("timed")) listOf(timed, retry, shout) else listOf(retry, timed, shout)
        var calls = 0
        println("$order:")
        val result = Invocation("Issuer.authorize", arrayOf("4111111111111111"), chain) {
            if (++calls < 3) throw IllegalStateException("issuer timed out")   // fails twice
            "auth-1111"
        }.proceed()
        println("  result $result after $calls calls, log ${log.calls()}")
    }
}

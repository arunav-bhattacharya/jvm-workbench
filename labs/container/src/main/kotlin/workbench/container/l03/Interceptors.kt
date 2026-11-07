package workbench.container.l03

import java.util.function.LongSupplier

/** Times the whole call, retries included, and records it once. */
class TimedInterceptor(private val log: CallLog, private val clock: LongSupplier) : Interceptor {
    override fun intercept(inv: Invocation): Any? {
        val start = clock.asLong
        var failed = true
        try {
            return inv.proceed().also { failed = false }
        } finally {
            log.record(inv.name, clock.asLong - start, failed)
        }
    }
}

/** Calls the rest of the chain again while it throws one of [retryOn], up to [attempts] calls in all. */
class RetryInterceptor(val attempts: Int, val retryOn: List<Class<out Throwable>>) : Interceptor {
    override fun intercept(inv: Invocation): Any? {
        var attempt = 1
        while (true) {
            try {
                return inv.proceed()                                  // 1. one more run of the method
            } catch (e: Throwable) {
                // 2. give up on the last attempt, or on a failure nobody said was worth retrying
                if (attempt >= attempts || retryOn.none { it.isInstance(e) }) throw e
                attempt++
            }
        }
    }
}

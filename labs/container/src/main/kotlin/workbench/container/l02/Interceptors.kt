package workbench.container.l02

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

/**
 * Calls the rest of the chain again while it throws one of [retryOn], up to [attempts] calls in all.
 * Call `inv.proceed()` in a loop. Rethrow the exception unchanged when it isn't an instance of any
 * class in [retryOn], or when this was the last attempt. `attempts = 3` means at most 3 calls.
 */
class RetryInterceptor(val attempts: Int, val retryOn: List<Class<out Throwable>>) : Interceptor {
    override fun intercept(inv: Invocation): Any? =
        TODO("call inv.proceed() again on a listed failure, at most attempts times")
}

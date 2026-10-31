package workbench.concurrency.scratch

import java.util.function.Supplier

class AuthRequest(val id: String)
class AuthResult
class IssuerTimeoutException : RuntimeException()
class AuthCancelledException(id: String, cause: Throwable) : RuntimeException(id, cause)
object issuer { fun authorize(r: AuthRequest): AuthResult = AuthResult() }
object log { fun warn(m: String, e: Throwable) {} }

fun authorizeOld(req: AuthRequest): AuthResult {
    var attempt = 1
    while (true) {
        try {
            return issuer.authorize(req)
        } catch (e: IssuerTimeoutException) {
            try {
                Thread.sleep(200L * attempt)
            } catch (ie: InterruptedException) {
                log.warn("interrupted during back-off", ie)   // and loop again
            }
        }
        attempt++
    }
}

fun authorizeNew(req: AuthRequest): AuthResult {
    var attempt = 1
    while (true) {
        try {
            return issuer.authorize(req)
        } catch (e: IssuerTimeoutException) {
            if (attempt == 3) throw e                          // 1. bounded retries
            try {
                Thread.sleep(200L * attempt)
            } catch (ie: InterruptedException) {
                Thread.currentThread().interrupt()             // 2. restore the request
                throw AuthCancelledException(req.id, ie)       // 3. stop, and say why
            }
        }
        attempt++
    }
}

fun drill(source: Supplier<List<String>>) {
    val poller = Runnable {
        try {
            while (!Thread.currentThread().isInterrupted) {
                val batch = source.get()
                batch.forEach(::println)
                if (batch.isEmpty()) Thread.sleep(100)
            }
        } catch (e: InterruptedException) {
            Thread.currentThread().interrupt()   // sleep cleared it; put it back
        }
    }
}

class Flusher {
    fun flushMetrics() {}
    fun start() {
        val flusher = Thread(this::flushMetrics, "metrics-flusher")
        flusher.isDaemon = true      // before start(), or you get IllegalThreadStateException
        flusher.start()
    }
}

fun backoff(backoffMillis: Long) {
    try {
        Thread.sleep(backoffMillis)
    } catch (e: InterruptedException) {
        Thread.currentThread().interrupt()    // put the request back
        return                                // then stop, or throw your own exception
    }
}

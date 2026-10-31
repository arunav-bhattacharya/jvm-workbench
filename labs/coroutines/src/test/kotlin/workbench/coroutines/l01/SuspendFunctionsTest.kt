package workbench.coroutines.l01

import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.cancelAndJoin
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.currentTime
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicReference
import kotlin.concurrent.thread
import kotlin.time.Duration.Companion.seconds

/** A fake SDK. If [reply] is set, it answers on a separate thread, like the real one. */
private class FakeIssuer(private val reply: ((AuthCallback) -> Unit)? = null) : CardIssuerClient {
    val requests = CopyOnWriteArrayList<AuthRequest>()
    val cancels = AtomicInteger()
    val callback = AtomicReference<AuthCallback>()

    override fun authorize(request: AuthRequest, callback: AuthCallback): InFlight {
        requests += request
        this.callback.set(callback)
        reply?.let { r -> thread(name = "issuer-sdk") { r(callback) } }
        return InFlight { cancels.incrementAndGet() }
    }
}

@OptIn(ExperimentalCoroutinesApi::class)
class SuspendFunctionsTest {
    private val request = AuthRequest("tok_4242", 12_000)
    private val approved = Authorization("A1B2C3", 12_000)

    @Test
    fun `authorizeAwait returns the authorization the issuer approves`() = runTest(timeout = 10.seconds) {
        val issuer = FakeIssuer { it.onApproved(approved) }
        assertThat(issuer.authorizeAwait(request)).isEqualTo(approved)
        assertThat(issuer.requests).containsExactly(request)
    }

    @Test
    fun `authorizeAwait throws the error the issuer reports`() = runTest(timeout = 10.seconds) {
        val issuer = FakeIssuer { it.onFailed(IssuerDeclinedException("insufficient funds")) }
        val thrown = try {
            issuer.authorizeAwait(request)
            null
        } catch (e: IssuerDeclinedException) {
            e
        }
        assertThat(thrown).isNotNull()
        assertThat(thrown!!.reason).isEqualTo("insufficient funds")
    }

    @Test
    fun `cancelling the caller cancels the request in flight`() = runTest(timeout = 10.seconds) {
        val issuer = FakeIssuer(reply = null) // never answers on its own
        val job = launch { issuer.authorizeAwait(request) }
        runCurrent() // the coroutine starts, sends the request and suspends
        assertThat(issuer.requests).hasSize(1)

        job.cancelAndJoin() // hangs here if the wait is not cancellable

        assertThat(job.isCancelled).isTrue()
        assertThat(issuer.cancels.get()).`as`("InFlight.cancel() calls").isEqualTo(1)
    }

    @Test
    fun `a late reply after cancellation is ignored`() = runTest(timeout = 10.seconds) {
        val issuer = FakeIssuer(reply = null)
        val job = launch { issuer.authorizeAwait(request) }
        runCurrent()
        job.cancelAndJoin()

        val lateError = AtomicReference<Throwable>()
        thread { runCatching { issuer.callback.get().onApproved(approved) }.onFailure(lateError::set) }.join()

        assertThat(lateError.get()).`as`("exception from the late callback").isNull()
        assertThat(job.isCancelled).isTrue()
    }

    @Test
    fun `pauseBeforeRetry lets other coroutines run while it waits`() = runTest {
        val log = CopyOnWriteArrayList<String>()
        repeat(3) { i ->
            launch {
                log += "start $i"
                pauseBeforeRetry(200)
                log += "end $i"
            }
        }
        advanceUntilIdle()
        // all three wait at the same time, on one thread, so they all start before any ends
        assertThat(log).containsExactly("start 0", "start 1", "start 2", "end 0", "end 1", "end 2")
        assertThat(currentTime).`as`("virtual time").isEqualTo(200)
    }
}

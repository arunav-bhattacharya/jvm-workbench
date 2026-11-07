package workbench.coroutines.l11

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.awaitCancellation
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withTimeoutOrNull
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import reactor.test.StepVerifier
import java.io.IOException
import java.util.concurrent.CancellationException
import java.util.concurrent.CompletableFuture
import java.util.concurrent.CountDownLatch
import java.util.concurrent.ExecutionException
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import kotlin.time.Duration.Companion.seconds

/** Builds facades for JavaCallerTest: Java can't easily write a Kotlin suspend lambda. */
object JavaFixtures {
    @JvmStatic
    fun approvingFacade(): AuthorizationFacade = AuthorizationFacade({ delay(10); Decision.APPROVED })
}

class JavaInteropTest {
    private val req = AuthRequest("pay-1", 4_250)

    // ---- AuthorizationFacade: suspend code for Java callers ----

    @Test
    fun `authorizeAsync completes the future with the decision`() {
        AuthorizationFacade({ delay(50); Decision.APPROVED }).use { facade ->
            assertThat(facade.authorizeAsync(req).get(5, TimeUnit.SECONDS)).isEqualTo(Decision.APPROVED)
        }
    }

    @Test
    fun `a failure reaches the Java caller as the cause of an ExecutionException`() {
        AuthorizationFacade({ throw IOException("issuer unreachable") }).use { facade ->
            val thrown = runCatching { facade.authorizeAsync(req).get(5, TimeUnit.SECONDS) }.exceptionOrNull()
            assertThat(thrown).isInstanceOf(ExecutionException::class.java)
            assertThat(thrown!!.cause).isInstanceOf(IOException::class.java).hasMessage("issuer unreachable")
        }
    }

    /** An authorization that waits for the issuer until it is cancelled (or gives up after 3 s). */
    private class Waiting {
        val started = CountDownLatch(1)
        val cancelled = CountDownLatch(1)
        val authorize: suspend (AuthRequest) -> Decision = {
            started.countDown()
            try {
                withTimeoutOrNull(3.seconds) { awaitCancellation() } // bounded, so a stub can't hang the build
                Decision.DECLINED
            } catch (e: kotlin.coroutines.cancellation.CancellationException) {
                cancelled.countDown()
                throw e
            }
        }
    }

    @Test
    fun `cancelling the future cancels the authorization coroutine`() {
        val w = Waiting()
        AuthorizationFacade(w.authorize).use { facade ->
            val future = facade.authorizeAsync(req)
            assertThat(w.started.await(5, TimeUnit.SECONDS)).isTrue()
            future.cancel(true)
            assertThat(w.cancelled.await(2, TimeUnit.SECONDS)).`as`("the coroutine saw the cancel").isTrue()
        }
    }

    @Test
    fun `close cancels the authorizations still running`() {
        val w = Waiting()
        val facade = AuthorizationFacade(w.authorize)
        val future = facade.authorizeAsync(req)
        assertThat(w.started.await(5, TimeUnit.SECONDS)).isTrue()
        facade.close()
        assertThat(w.cancelled.await(2, TimeUnit.SECONDS)).`as`("the coroutine saw the cancel").isTrue()
        val thrown = runCatching { future.get(2, TimeUnit.SECONDS) }.exceptionOrNull()
        assertThat(thrown).`as`("what the Java caller gets").isInstanceOf(CancellationException::class.java)
    }

    // ---- scoreAwait: a CompletableFuture inside suspend code ----

    @Test
    fun `scoreAwait returns the score when the future completes`() = runBlocking<Unit> {
        val client = LegacyFraudClient { CompletableFuture.supplyAsync { Thread.sleep(20); 37 } }
        assertThat(client.scoreAwait(req)).isEqualTo(37)
    }

    @Test
    fun `cancelling the caller cancels the client's future`() = runBlocking<Unit> {
        val pending = CompletableFuture<Int>()
        val asked = CountDownLatch(1)
        val client = LegacyFraudClient { asked.countDown(); pending }
        val caller = launch(Dispatchers.Default) { client.scoreAwait(req) }
        assertThat(asked.await(5, TimeUnit.SECONDS)).isTrue()
        caller.cancel()
        val stopped = withTimeoutOrNull(2.seconds) { caller.join() } != null
        pending.complete(0) // releases a thread that is stuck in get()
        assertThat(stopped).`as`("the caller stopped within 2 s of the cancel").isTrue()
        assertThat(pending.isCancelled).`as`("the client's future was cancelled").isTrue()
    }

    // ---- quoteMono: a coroutine as a Reactor Mono ----

    @Test
    fun `quoteMono is cold and asks again for every subscriber`() {
        val calls = AtomicInteger()
        val mono = quoteMono({ calls.incrementAndGet(); delay(10); Quote("north", 180) }, req)
        Thread.sleep(100)
        assertThat(calls.get()).`as`("quotes requested before anyone subscribed").isZero()
        StepVerifier.create(mono).expectNext(Quote("north", 180)).verifyComplete()
        StepVerifier.create(mono).expectNext(Quote("north", 180)).verifyComplete()
        assertThat(calls.get()).`as`("quotes requested for two subscribers").isEqualTo(2)
    }

    @Test
    fun `quoteMono completes empty when nobody quotes`() {
        StepVerifier.create(quoteMono({ null }, req)).verifyComplete()
    }

    @Test
    fun `disposing the subscription cancels the coroutine`() {
        val started = CountDownLatch(1)
        val cancelled = CountDownLatch(1)
        val mono = quoteMono({
            started.countDown()
            try {
                withTimeoutOrNull(3.seconds) { awaitCancellation() } // bounded, so a stub can't hang the build
                null
            } catch (e: kotlin.coroutines.cancellation.CancellationException) {
                cancelled.countDown()
                throw e
            }
        }, req)
        val subscription = mono.subscribe()
        assertThat(started.await(5, TimeUnit.SECONDS)).isTrue()
        subscription.dispose()
        assertThat(cancelled.await(2, TimeUnit.SECONDS)).isTrue()
    }
}

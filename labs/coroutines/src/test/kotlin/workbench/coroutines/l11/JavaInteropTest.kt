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

/** Builds doors for JavaCallerTest: Java can't easily write a Kotlin suspend lambda. */
object JavaFixtures {
    @JvmStatic
    fun servingDoor(): KitchenDoor = KitchenDoor({ delay(10); Outcome.SERVED })
}

class JavaInteropTest {
    private val order = Order("soup", 4)

    // ---- KitchenDoor: suspend code for Java callers ----

    @Test
    fun `cookAsync completes the future with the outcome`() {
        KitchenDoor({ delay(50); Outcome.SERVED }).use { door ->
            assertThat(door.cookAsync(order).get(5, TimeUnit.SECONDS)).isEqualTo(Outcome.SERVED)
        }
    }

    @Test
    fun `a failure reaches the Java caller as the cause of an ExecutionException`() {
        KitchenDoor({ throw IOException("the stove won't light") }).use { door ->
            val thrown = runCatching { door.cookAsync(order).get(5, TimeUnit.SECONDS) }.exceptionOrNull()
            assertThat(thrown).isInstanceOf(ExecutionException::class.java)
            assertThat(thrown!!.cause).isInstanceOf(IOException::class.java).hasMessage("the stove won't light")
        }
    }

    /** An order that cooks until it is cancelled (or gives up after 3 s). */
    private class Waiting {
        val started = CountDownLatch(1)
        val cancelled = CountDownLatch(1)
        val cook: suspend (Order) -> Outcome = {
            started.countDown()
            try {
                withTimeoutOrNull(3.seconds) { awaitCancellation() } // bounded, so a stub can't hang the build
                Outcome.REFUSED
            } catch (e: kotlin.coroutines.cancellation.CancellationException) {
                cancelled.countDown()
                throw e
            }
        }
    }

    @Test
    fun `cancelling the future cancels the cooking coroutine`() {
        val w = Waiting()
        KitchenDoor(w.cook).use { door ->
            val future = door.cookAsync(order)
            assertThat(w.started.await(5, TimeUnit.SECONDS)).isTrue()
            future.cancel(true)
            assertThat(w.cancelled.await(2, TimeUnit.SECONDS)).`as`("the coroutine saw the cancel").isTrue()
        }
    }

    @Test
    fun `close cancels the orders still cooking`() {
        val w = Waiting()
        val door = KitchenDoor(w.cook)
        val future = door.cookAsync(order)
        assertThat(w.started.await(5, TimeUnit.SECONDS)).isTrue()
        door.close()
        assertThat(w.cancelled.await(2, TimeUnit.SECONDS)).`as`("the coroutine saw the cancel").isTrue()
        val thrown = runCatching { future.get(2, TimeUnit.SECONDS) }.exceptionOrNull()
        assertThat(thrown).`as`("what the Java caller gets").isInstanceOf(CancellationException::class.java)
    }

    // ---- loavesLeftAwait: a CompletableFuture inside suspend code ----

    @Test
    fun `loavesLeftAwait returns the count when the future completes`() = runBlocking<Unit> {
        val bakery = JavaBakery { CompletableFuture.supplyAsync { Thread.sleep(20); 37 } }
        assertThat(bakery.loavesLeftAwait("rye")).isEqualTo(37)
    }

    @Test
    fun `cancelling the caller cancels the bakery's future`() = runBlocking<Unit> {
        val pending = CompletableFuture<Int>()
        val asked = CountDownLatch(1)
        val bakery = JavaBakery { asked.countDown(); pending }
        val caller = launch(Dispatchers.Default) { bakery.loavesLeftAwait("rye") }
        assertThat(asked.await(5, TimeUnit.SECONDS)).isTrue()
        caller.cancel()
        val stopped = withTimeoutOrNull(2.seconds) { caller.join() } != null
        pending.complete(0) // releases a thread that is stuck in get()
        assertThat(stopped).`as`("the caller stopped within 2 s of the cancel").isTrue()
        assertThat(pending.isCancelled).`as`("the bakery's future was cancelled").isTrue()
    }

    // ---- recipeMono: a coroutine as a Reactor Mono ----

    @Test
    fun `recipeMono is cold and looks the recipe up again for every subscriber`() {
        val lookups = AtomicInteger()
        val mono = recipeMono({ lookups.incrementAndGet(); delay(10); Recipe("soup", 40) }, "soup")
        Thread.sleep(100)
        assertThat(lookups.get()).`as`("lookups before anyone subscribed").isZero()
        StepVerifier.create(mono).expectNext(Recipe("soup", 40)).verifyComplete()
        StepVerifier.create(mono).expectNext(Recipe("soup", 40)).verifyComplete()
        assertThat(lookups.get()).`as`("lookups for two subscribers").isEqualTo(2)
    }

    @Test
    fun `recipeMono completes empty when the book has no recipe`() {
        StepVerifier.create(recipeMono({ null }, "dragon stew")).verifyComplete()
    }

    @Test
    fun `disposing the subscription cancels the coroutine`() {
        val started = CountDownLatch(1)
        val cancelled = CountDownLatch(1)
        val mono = recipeMono({
            started.countDown()
            try {
                withTimeoutOrNull(3.seconds) { awaitCancellation() } // bounded, so a stub can't hang the build
                null
            } catch (e: kotlin.coroutines.cancellation.CancellationException) {
                cancelled.countDown()
                throw e
            }
        }, "soup")
        val subscription = mono.subscribe()
        assertThat(started.await(5, TimeUnit.SECONDS)).isTrue()
        subscription.dispose()
        assertThat(cancelled.await(2, TimeUnit.SECONDS)).isTrue()
    }
}

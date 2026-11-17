package workbench.coroutines.l04

import kotlinx.coroutines.CoroutineName
import kotlinx.coroutines.asCoroutineDispatcher
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeout
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.Test
import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import kotlin.time.Duration.Companion.seconds

class DispatchersTest {
    // two named single-thread dispatchers stand in for IO and Default, so the test can see where code ran
    private val ioPool = Executors.newSingleThreadExecutor { r -> Thread(r, "test-io") }
    private val cpuPool = Executors.newSingleThreadExecutor { r -> Thread(r, "test-cpu") }
    private val io = ioPool.asCoroutineDispatcher()
    private val cpu = cpuPool.asCoroutineDispatcher()

    @AfterEach
    fun closePools() {
        io.close()
        cpu.close()
    }

    private class RecordingBook(val threads: MutableList<String>) : BlockingRecipeBook {
        override fun loadSteps(dish: String): List<Step> {
            threads += "load:" + Thread.currentThread().name
            return listOf(Step(dish, "chop the onions"), Step(dish, "simmer for 20 minutes"))
        }
    }

    private class RecordingPrinter(val threads: MutableList<String>) : CardPrinter {
        override fun render(steps: List<Step>): ByteArray {
            threads += "render:" + Thread.currentThread().name
            return steps.joinToString("\n") { "${it.dish}: ${it.text}" }.toByteArray()
        }
    }

    // ---- RecipeCardService ----

    @Test
    fun `printCard loads steps on the IO dispatcher and renders on the CPU dispatcher`() = runTest {
        val threads = CopyOnWriteArrayList<String>()
        val service = RecipeCardService(RecordingBook(threads), RecordingPrinter(threads), io, cpu)

        val card = service.printCard("soup")

        assertThat(String(card)).isEqualTo("soup: chop the onions\nsoup: simmer for 20 minutes")
        assertThat(threads).containsExactly("load:test-io", "render:test-cpu")
    }

    @Test
    fun `printCard hands the result back on the caller's thread`() = runBlocking<Unit> {
        val threads = CopyOnWriteArrayList<String>()
        val service = RecipeCardService(RecordingBook(threads), RecordingPrinter(threads), io, cpu)
        val callerThread = Thread.currentThread().name

        service.printCard("soup")

        assertThat(Thread.currentThread().name).isEqualTo(callerThread)
        assertThat(threads).doesNotContain("load:$callerThread", "render:$callerThread")
    }

    // ---- bakeryDispatcher ----

    @Test
    fun `bakeryDispatcher is named bakery`() {
        assertThat(bakeryDispatcher().toString()).isEqualTo("bakery")
    }

    @Test
    fun `bakeryDispatcher lets 20 blocking calls run at the same time`() = runBlocking<Unit> {
        val dispatcher = bakeryDispatcher()
        val allIn = CountDownLatch(20)
        val met = withTimeout(10.seconds) {
            (1..20).map {
                async(dispatcher) {
                    allIn.countDown()
                    allIn.await(5, TimeUnit.SECONDS) // only true if all 20 are blocked here together
                }
            }.awaitAll()
        }
        assertThat(met).`as`("calls that saw all 20 running together").containsOnly(true)
    }

    @Test
    fun `bakeryDispatcher never runs more than 20 calls at once`() = runBlocking<Unit> {
        val dispatcher = bakeryDispatcher()
        val active = AtomicInteger()
        val peak = AtomicInteger()
        withTimeout(10.seconds) {
            coroutineScope {
                repeat(60) {
                    launch(dispatcher) {
                        val now = active.incrementAndGet()
                        peak.accumulateAndGet(now, ::maxOf)
                        Thread.sleep(30) // a blocking call to the bakery
                        active.decrementAndGet()
                    }
                }
            }
        }
        assertThat(peak.get()).`as`("peak concurrent calls").isLessThanOrEqualTo(20).isGreaterThan(1)
    }

    // ---- context elements ----

    @Test
    fun `withGuest makes the guest visible inside the block`() = runTest {
        assertThat(currentGuest()).isNull()
        val seen = withGuest("ana") { currentGuest() }
        assertThat(seen).isEqualTo("ana")
        assertThat(currentGuest()).`as`("after the block").isNull()
    }

    @Test
    fun `withGuest names the coroutine and child coroutines inherit both elements`() = runTest {
        val seen = CopyOnWriteArrayList<String>()
        withGuest("ana") {
            launch {
                val ctx = currentCoroutineContext()
                seen += "${ctx[ForGuest]?.name} ${ctx[CoroutineName]?.name}"
            }
        }
        assertThat(seen).containsExactly("ana for-ana")
    }

    @Test
    fun `a nested withGuest replaces the outer guest for its block only`() = runTest {
        val seen = withGuest("ana") {
            val inner = withGuest("ben") { currentGuest() }
            listOf(inner, currentGuest())
        }
        assertThat(seen).containsExactly("ben", "ana")
    }
}

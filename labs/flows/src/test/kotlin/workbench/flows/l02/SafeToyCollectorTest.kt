package workbench.flows.l02

import kotlinx.coroutines.CoroutineName
import kotlinx.coroutines.cancel
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.withContext
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import kotlin.coroutines.EmptyCoroutineContext

class SafeToyCollectorTest {

    private suspend fun <T> ToyFlow<T>.toList(): List<T> {
        val out = mutableListOf<T>()
        collect { out += it }
        return out
    }

    // ---- the happy path is unchanged ----

    @Test
    fun `a safe toy flow delivers every value, still inside emit`() = runTest {
        val events = mutableListOf<String>()
        safeToyFlow {
            for (id in 1..3) {
                emit(id)
                events += "emit $id returned"
            }
        }.collect { events += "got $it" }
        assertThat(events).containsExactly("got 1", "emit 1 returned", "got 2", "emit 2 returned", "got 3", "emit 3 returned")
    }

    // ---- check: same context ----

    @Test
    fun `emitting from another dispatcher is refused`() = runTest {
        val other = StandardTestDispatcher(testScheduler, name = "acquirer-io")
        val got = mutableListOf<Int>()
        val thrown = runCatching {
            safeToyFlow { withContext(other) { emit(1) } }.collect { got += it }
        }.exceptionOrNull()
        assertThat(thrown).isInstanceOf(IllegalStateException::class.java).hasMessageStartingWith("Flow invariant is violated")
        assertThat(got).`as`("values the collector saw").isEmpty()
    }

    @Test
    fun `emitting under another coroutine name is refused too`() = runTest {
        val thrown = runCatching {
            safeToyFlow { withContext(CoroutineName("other")) { emit(1) } }.toList()
        }.exceptionOrNull()
        assertThat(thrown).isInstanceOf(IllegalStateException::class.java).hasMessageStartingWith("Flow invariant is violated")
    }

    @Test
    fun `coroutineScope and withContext(EmptyCoroutineContext) keep the context, so they are allowed`() = runTest {
        assertThat(safeToyFlow { coroutineScope { emit(1) } }.toList()).containsExactly(1)
        assertThat(safeToyFlow { withContext(EmptyCoroutineContext) { emit(2) } }.toList()).containsExactly(2)
    }

    // ---- check: exception transparency ----

    @Test
    fun `after the collector threw, the next emit is refused and the message names the first failure`() = runTest {
        val f = safeToyFlow {
            emit(4250L)
            try {
                emit(-990L)
            } catch (e: IllegalArgumentException) {
                emit(12000L)                      // "log and post the next one": not allowed
            }
        }
        val thrown = runCatching {
            f.collect { cents -> require(cents >= 0) { "negative amount $cents" } }
        }.exceptionOrNull()
        assertThat(thrown).isInstanceOf(IllegalStateException::class.java)
            .hasMessageStartingWith("Flow exception transparency is violated")
            .hasMessageContaining("negative amount -990")
    }

    @Test
    fun `a try-catch around every emit swallows the check too, and the rest of the batch is lost`() = runTest {
        val warnings = mutableListOf<String>()
        val postings = safeToyFlow {
            for (cents in listOf(4250L, -990L, 12000L)) {
                try {
                    emit(cents)
                } catch (e: Exception) {
                    warnings += e.message.orEmpty()   // "logs and continues"
                }
            }
        }
        val posted = mutableListOf<Long>()
        postings.collect { cents -> require(cents >= 0) { "negative amount $cents" }; posted += cents }
        assertThat(posted).`as`("postings that reached the ledger").containsExactly(4250L)
        assertThat(warnings).hasSize(2)
        assertThat(warnings[0]).isEqualTo("negative amount -990")
        assertThat(warnings[1]).startsWith("Flow exception transparency is violated")
    }

    // ---- check: cancellation ----

    @Test
    fun `a collector that cancels itself without suspending gets no more values`() = runTest {
        val unchecked = mutableListOf<Int>()
        launch { toyFlow { for (i in 1..5) emit(i) }.collect { v -> unchecked += v; if (v == 3) cancel() } }.join()
        assertThat(unchecked).`as`("the plain toy flow has no check").containsExactly(1, 2, 3, 4, 5)

        val checked = mutableListOf<Int>()
        launch { safeToyFlow { for (i in 1..5) emit(i) }.collect { v -> checked += v; if (v == 3) cancel() } }.join()
        assertThat(checked).`as`("the safe toy flow calls ensureActive on each emit").containsExactly(1, 2, 3)
    }
}

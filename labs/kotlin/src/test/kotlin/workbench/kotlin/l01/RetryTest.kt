package workbench.kotlin.l01

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.assertj.core.api.Assertions.catchThrowable
import org.junit.jupiter.api.Test
import java.util.concurrent.ExecutionException
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit

class RetryTest {

    @Test
    fun `retry returns the first successful result and stops there`() {
        var calls = 0
        val result = Callers.retrying(5, { true }) { attempt ->
            calls++
            if (attempt < 3) throw IllegalStateException("issuer timeout $attempt") else "approved@$attempt"
        }
        assertThat(result).isEqualTo("approved@3")
        assertThat(calls).isEqualTo(3)
    }

    @Test
    fun `retry gives up after maxAttempts, with the last failure as cause and the earlier ones suppressed`() {
        var calls = 0
        val thrown = catchThrowable {
            Callers.retrying(3, { true }) { attempt -> calls++; throw IllegalStateException("fail $attempt") }
        }
        assertThat(thrown).isInstanceOf(RetryExhaustedException::class.java)
        val ex = thrown as RetryExhaustedException
        assertThat(ex.attempts).isEqualTo(3)
        assertThat(ex.cause).hasMessage("fail 3")
        assertThat(ex.suppressed.map { it.message }).containsExactly("fail 1", "fail 2")
        assertThat(calls).isEqualTo(3)
    }

    @Test
    fun `retry stops at once when shouldRetry says no`() {
        var calls = 0
        val thrown = catchThrowable {
            Callers.retrying(5, { it !is IllegalArgumentException }) { calls++; throw IllegalArgumentException("bad card number") }
        }
        assertThat(thrown).isInstanceOf(RetryExhaustedException::class.java)
        assertThat((thrown as RetryExhaustedException).attempts).isEqualTo(1)
        assertThat(thrown.suppressed).isEmpty()
        assertThat(calls).isEqualTo(1)
    }

    @Test
    fun `retry rejects maxAttempts below 1 before running the block`() {
        var calls = 0
        assertThatThrownBy { Callers.retrying(0, { true }) { calls++ } }
            .isInstanceOf(IllegalArgumentException::class.java)
        assertThat(calls).isEqualTo(0)
    }

    @Test
    fun `a return inside the block returns from the calling function`() {
        val calls = mutableListOf<String>()
        var timedOut = false
        val card = Callers.firstApproved(listOf("card-A", "card-B", "card-C")) { c ->
            calls += c
            when {
                c == "card-A" && !timedOut -> { timedOut = true; throw IllegalStateException("timeout") }
                c == "card-B" -> "APPROVED"
                else -> "DECLINED"
            }
        }
        assertThat(card).isEqualTo("card-B")
        // card-A timed out once and was retried, then declined; card-C was never tried
        assertThat(calls).containsExactly("card-A", "card-A", "card-B")
    }

    @Test
    fun `retryAsync runs the attempts on the executor and completes with the result`() {
        val pool = Executors.newSingleThreadExecutor { Thread(it, "retry-worker") }
        try {
            val threads = mutableListOf<String>()
            val future = Callers.retryingAsync(pool, 3) { attempt ->
                synchronized(threads) { threads += Thread.currentThread().name }
                if (attempt == 1) throw IllegalStateException("timeout") else "captured@$attempt"
            }
            assertThat(future.get(5, TimeUnit.SECONDS)).isEqualTo("captured@2")
            assertThat(threads).containsExactly("retry-worker", "retry-worker")
        } finally {
            pool.shutdownNow()
        }
    }

    @Test
    fun `retryAsync completes exceptionally with RetryExhaustedException`() {
        val pool = Executors.newSingleThreadExecutor()
        try {
            val future = Callers.retryingAsync<String>(pool, 2) { throw IllegalStateException("issuer down") }
            assertThatThrownBy { future.get(5, TimeUnit.SECONDS) }
                .isInstanceOf(ExecutionException::class.java)
                .hasCauseInstanceOf(RetryExhaustedException::class.java)
        } finally {
            pool.shutdownNow()
        }
    }
}

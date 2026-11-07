package workbench.coroutines.l06

import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.cancelAndJoin
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.advanceTimeBy
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.currentTime
import kotlinx.coroutines.test.runTest
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import java.io.IOException
import java.util.concurrent.CopyOnWriteArrayList
import kotlin.time.Duration.Companion.seconds

@OptIn(ExperimentalCoroutinesApi::class)
class ExceptionsTest {

    // ---- notifyAll: fan-out inside the request ----

    @Test
    fun `notifyAll delivers on every channel when all succeed`() = runTest {
        val sent = CopyOnWriteArrayList<Channel>()
        val senders = Channel.entries.associateWith { ch -> Sender { delay(100); sent += ch } }
        val outcomes = notifyAll("pay-1", senders, 2.seconds)
        assertThat(outcomes).containsOnlyKeys(*Channel.entries.toTypedArray())
        assertThat(outcomes.values).containsOnly(Outcome.Delivered)
        assertThat(currentTime).`as`("virtual ms: sent at the same time").isEqualTo(100)
    }

    @Test
    fun `one failing channel does not stop the others`() = runTest {
        val sent = CopyOnWriteArrayList<Channel>()
        val senders = mapOf(
            Channel.EMAIL to Sender { delay(300); sent += Channel.EMAIL },
            Channel.SMS to Sender { delay(50); throw IOException("sms gateway down") },
            Channel.PUSH to Sender { delay(100); sent += Channel.PUSH },
        )
        val outcomes = notifyAll("pay-1", senders, 2.seconds)
        assertThat(outcomes).isEqualTo(
            mapOf(Channel.EMAIL to Outcome.Delivered, Channel.SMS to Outcome.Failed("sms gateway down"), Channel.PUSH to Outcome.Delivered)
        )
        assertThat(sent).containsExactlyInAnyOrder(Channel.EMAIL, Channel.PUSH)
        assertThat(currentTime).isEqualTo(300)
    }

    @Test
    fun `a channel slower than the timeout counts as failed`() = runTest {
        val senders = mapOf(
            Channel.EMAIL to Sender { delay(100) },
            Channel.SMS to Sender { delay(10_000) }, // a stuck gateway
        )
        val outcomes = notifyAll("pay-1", senders, 2.seconds)
        assertThat(outcomes).isEqualTo(mapOf(Channel.EMAIL to Outcome.Delivered, Channel.SMS to Outcome.Failed("timed out")))
        assertThat(currentTime).`as`("virtual ms: gave up on SMS at the timeout").isEqualTo(2_000)
    }

    @Test
    fun `cancelling the caller cancels every send`() = runTest {
        val sent = CopyOnWriteArrayList<Channel>()
        var outcomes: Map<Channel, Outcome>? = null
        val request = launch {
            outcomes = notifyAll("pay-1", Channel.entries.associateWith { ch -> Sender { delay(1_000); sent += ch } }, 5.seconds)
        }
        advanceTimeBy(500)
        request.cancelAndJoin()
        advanceUntilIdle()
        assertThat(sent).`as`("sends that finished after the caller left").isEmpty()
        assertThat(outcomes).`as`("a cancelled call returns no outcomes").isNull()
    }

    // ---- NotificationService: background work that outlives the request ----

    private class Recorder {
        val failures = CopyOnWriteArrayList<String>()
        val sent = CopyOnWriteArrayList<String>()
    }

    @Test
    fun `a failing notification does not cancel the others`() = runTest {
        val r = Recorder()
        val service = NotificationService(StandardTestDispatcher(testScheduler)) { id, e -> r.failures += "$id: ${e.message}" }
        service.notifyLater("pay-1") { delay(100); throw IOException("smtp refused") }
        service.notifyLater("pay-2") { delay(300); r.sent += it }
        advanceUntilIdle()
        assertThat(r.sent).containsExactly("pay-2")
        service.close()
    }

    @Test
    fun `a failure is reported with its payment id`() = runTest {
        val r = Recorder()
        val service = NotificationService(StandardTestDispatcher(testScheduler)) { id, e -> r.failures += "$id: ${e.message}" }
        service.notifyLater("pay-7") { delay(10); throw IOException("smtp refused") }
        advanceUntilIdle()
        assertThat(r.failures).containsExactly("pay-7: smtp refused")
        service.close()
    }

    @Test
    fun `the service keeps working after a failure`() = runTest {
        val r = Recorder()
        val service = NotificationService(StandardTestDispatcher(testScheduler)) { id, e -> r.failures += "$id: ${e.message}" }
        service.notifyLater("pay-1") { throw IOException("smtp refused") }
        advanceUntilIdle()
        service.notifyLater("pay-2") { delay(10); r.sent += it }
        advanceUntilIdle()
        assertThat(r.sent).`as`("notifications sent after the failure").containsExactly("pay-2")
        service.close()
    }

    @Test
    fun `close cancels pending notifications and waits for them`() = runTest {
        val r = Recorder()
        val cleanedUp = CopyOnWriteArrayList<String>()
        val service = NotificationService(StandardTestDispatcher(testScheduler)) { id, e -> r.failures += "$id: ${e.message}" }
        service.notifyLater("pay-1") { id -> try { delay(10_000); r.sent += id } finally { cleanedUp += id } }
        advanceTimeBy(100)
        assertThat(service.pending).`as`("pending before close").isEqualTo(1)
        service.close()
        assertThat(cleanedUp).`as`("cleaned up when close returned").containsExactly("pay-1")
        assertThat(r.sent).isEmpty()
        assertThat(service.pending).`as`("pending after close").isEqualTo(0)
        assertThat(r.failures).`as`("a cancel is not a failure").isEmpty()
    }
}

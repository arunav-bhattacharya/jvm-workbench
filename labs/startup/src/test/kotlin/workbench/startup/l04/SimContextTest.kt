package workbench.startup.l04

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test
import java.io.IOException

class SimContextTest {
    private val log = mutableListOf<String>()
    private val network = FakeNetwork()
    private val context = SimContext(network) { log += "snapshot" }

    /** A resource that logs its hooks and can be told to fail or to leave a socket open. */
    private inner class Recording(
        val name: String,
        val failBefore: Boolean = false,
        val failAfter: Boolean = false,
        val leaveOpen: Boolean = false,
    ) : Resource {
        private var socket: FakeSocket? = network.open("$name.example:443")

        override fun beforeCheckpoint() {
            log += "before:$name"
            if (failBefore) throw IOException("$name could not flush")
            if (!leaveOpen) socket?.close()
        }

        override fun afterRestore() {
            log += "after:$name"
            if (failAfter) throw IOException("$name could not reconnect")
            if (socket?.isOpen != true) socket = network.open("$name.example:443")
        }
    }

    @Test
    fun `checkpoint runs in reverse registration order and restore in registration order`() {
        listOf("pool", "consumer", "cache").forEach { context.register(Recording(it)) }
        context.checkpointRestore()
        assertThat(log).containsExactly(
            "before:cache", "before:consumer", "before:pool", "snapshot",
            "after:pool", "after:consumer", "after:cache")
    }

    @Test
    fun `an open socket fails the checkpoint, nothing is snapshotted, and everyone is restored`() {
        context.register(Recording("pool"))
        context.register(Recording("consumer", leaveOpen = true))
        val e = assertThatThrownBy { context.checkpointRestore() }.isInstanceOf(CheckpointException::class.java)
        e.satisfies({ ex ->
            assertThat(ex.suppressed).hasSize(1)
            assertThat(ex.suppressed[0]).isInstanceOf(IllegalStateException::class.java).hasMessageContaining("consumer.example")
        })
        assertThat(log).doesNotContain("snapshot")
        assertThat(log).containsExactly("before:consumer", "before:pool", "after:pool", "after:consumer")
    }

    @Test
    fun `a failing beforeCheckpoint does not stop the others, and its exception is suppressed`() {
        context.register(Recording("pool"))
        context.register(Recording("consumer", failBefore = true, leaveOpen = true))
        context.register(Recording("cache"))
        val e = assertThatThrownBy { context.checkpointRestore() }.isInstanceOf(CheckpointException::class.java)
        e.satisfies({ ex ->
            assertThat(ex.suppressed.map { it.message }).contains("consumer could not flush")
        })
        assertThat(log).containsExactly(
            "before:cache", "before:consumer", "before:pool",
            "after:pool", "after:consumer", "after:cache")
    }

    @Test
    fun `a failing afterRestore comes after the snapshot, as a RestoreException, and the others still restore`() {
        context.register(Recording("pool", failAfter = true))
        context.register(Recording("cache"))
        val e = assertThatThrownBy { context.checkpointRestore() }.isInstanceOf(RestoreException::class.java)
        e.satisfies({ ex ->
            assertThat(ex.suppressed.map { it.message }).containsExactly("pool could not reconnect")
        })
        assertThat(log).containsExactly("before:cache", "before:pool", "snapshot", "after:pool", "after:cache")
    }
}

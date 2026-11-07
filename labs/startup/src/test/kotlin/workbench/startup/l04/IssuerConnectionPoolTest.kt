package workbench.startup.l04

import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test

class IssuerConnectionPoolTest {
    private val network = FakeNetwork()
    private var openAtSnapshot: List<FakeSocket>? = null
    private val context = SimContext(network) { openAtSnapshot = network.openSockets() }

    @Test
    fun `borrow hands out the pool's open connections in turn`() {
        val pool = IssuerConnectionPool(network, 3, context)
        val first = (1..3).map { pool.borrow() }
        assertThat(first.map { it.id }).containsExactly(1, 2, 3)
        assertThat(pool.borrow().id).isEqualTo(1)
        assertThat(first).allMatch { it.isOpen }
    }

    @Test
    fun `the pool registers itself, so a checkpoint succeeds with nothing open`() {
        IssuerConnectionPool(network, 3, context)
        context.checkpointRestore()                       // throws CheckpointException if sockets stay open
        assertThat(openAtSnapshot).isNotNull.isEmpty()
    }

    @Test
    fun `after restore the pool hands out new, open connections`() {
        val pool = IssuerConnectionPool(network, 3, context)
        val before = (1..3).map { pool.borrow() }
        context.checkpointRestore()
        val after = (1..3).map { pool.borrow() }
        assertThat(before).allMatch { !it.isOpen }
        assertThat(after).allMatch { it.isOpen }
        assertThat(after.map { it.id }).doesNotContainAnyElementsOf(before.map { it.id })
        assertThat(after.map { it.peer }).containsOnly("issuer.example:443")
    }

    @Test
    fun `a second checkpoint works too`() {
        val pool = IssuerConnectionPool(network, 2, context)
        context.checkpointRestore()
        context.checkpointRestore()
        assertThat(network.openSockets()).hasSize(2)
        assertThat(pool.borrow().isOpen).isTrue()
    }
}

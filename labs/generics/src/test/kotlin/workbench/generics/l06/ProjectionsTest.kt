package workbench.generics.l06

import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import workbench.generics.JavaSignatures
import java.util.ArrayDeque

class ProjectionsTest {

    @Test
    fun `copyInto appends every item in order and returns the count`() {
        val from = mutableListOf(1_200, 350, 99)
        val to = mutableListOf(1)
        assertThat(copyInto(from, to)).isEqualTo(3)
        assertThat(to).containsExactly(1, 1_200, 350, 99)
        assertThat(from).containsExactly(1_200, 350, 99)     // only read, never changed
    }

    @Test
    fun `copyInto reads from an out-projection and writes to an in-projection`() {
        val k = "workbench.generics.l06.ProjectionsKt"
        assertThat(JavaSignatures.paramText(k, "copyInto", 0)).`as`("from (only read)").isEqualTo("List<? extends T>")
        assertThat(JavaSignatures.paramText(k, "copyInto", 1)).`as`("to (only written)").isEqualTo("List<? super T>")
    }

    @Test
    fun `fillWith appends count copies of the value`() {
        val target = mutableListOf("EUR")
        fillWith(target, "pending", 3)
        assertThat(target).containsExactly("EUR", "pending", "pending", "pending")
    }

    @Test
    fun `fillWith only writes, so its target is an in-projection`() {
        assertThat(JavaSignatures.paramText("workbench.generics.l06.ProjectionsKt", "fillWith", 0)).isEqualTo("List<? super T>")
    }

    @Test
    fun `sumAll accepts a List of Int and a List of Double with no projection`() {
        val ints: List<Int> = listOf(1_200, 350, 99)
        val doubles: List<Double> = listOf(0.5, 0.25)
        assertThat(sumAll(ints)).isEqualTo(1_649.0)
        assertThat(sumAll(doubles)).isEqualTo(0.75)
        assertThat(sumAll(emptyList())).isEqualTo(0.0)
    }

    @Test
    fun `drainTo moves everything in queue order and empties the queue`() {
        val from = ArrayDeque(listOf(10, 20, 30))
        val to = ArrayList<Int>()
        assertThat(Transfers.drainTo(from, to)).isEqualTo(3)
        assertThat(to).containsExactly(10, 20, 30)
        assertThat(from).isEmpty()
    }

    @Test
    fun `drainTo uses Producer Extends and Consumer Super`() {
        val k = "workbench.generics.l06.Transfers"
        assertThat(JavaSignatures.paramText(k, "drainTo", 0)).`as`("from").isEqualTo("Queue<? extends T>")
        assertThat(JavaSignatures.paramText(k, "drainTo", 1)).`as`("to").isEqualTo("Collection<? super T>")
    }
}

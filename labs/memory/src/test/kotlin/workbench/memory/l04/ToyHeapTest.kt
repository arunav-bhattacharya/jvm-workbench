package workbench.memory.l04

import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test

class ToyHeapTest {

    @Test
    fun `mark finds everything reachable through chains of references, and nothing else`() {
        val heap = ToyHeap()
        val request = heap.allocate()
        val photo = heap.allocate()
        val pixels = heap.allocate()
        val orphan = heap.allocate()
        heap.link(request, photo)
        heap.link(photo, pixels)
        assertThat(heap.mark(listOf(request))).containsExactlyInAnyOrder(request, photo, pixels)
        assertThat(heap.contains(orphan)).`as`("mark only looks; it frees nothing").isTrue()
    }

    @Test
    fun `mark stops on cycles`() {
        val heap = ToyHeap()
        val a = heap.allocate()
        val b = heap.allocate()
        heap.link(a, b)
        heap.link(b, a)
        assertThat(heap.mark(listOf(a))).containsExactlyInAnyOrder(a, b)
    }

    @Test
    fun `collect frees an unreachable cycle that reference counting would keep`() {
        val heap = ToyHeap()
        val root = heap.allocate()
        val x = heap.allocate()
        val y = heap.allocate()
        heap.link(x, y)                                     // x and y point at each other: each has one reference
        heap.link(y, x)
        assertThat(heap.collect(listOf(root))).containsExactlyInAnyOrder(x, y)
        assertThat(heap.size).isEqualTo(1)
    }

    @Test
    fun `a root survives even when nothing points at it`() {
        val heap = ToyHeap()
        val root = heap.allocate()
        assertThat(heap.collect(listOf(root))).isEmpty()
        assertThat(heap.contains(root)).isTrue()
    }

    @Test
    fun `clearing one reference frees everything that was only reachable through it`() {
        val heap = ToyHeap()
        val cache = heap.allocate()
        val entry = heap.allocate()
        val thumbnail = heap.allocate()
        val pixels = heap.allocate()
        heap.link(cache, entry)
        heap.link(entry, thumbnail)
        heap.link(thumbnail, pixels)
        assertThat(heap.collect(listOf(cache))).isEmpty()
        heap.unlink(cache, entry)                           // evict the entry
        assertThat(heap.collect(listOf(cache))).containsExactlyInAnyOrder(entry, thumbnail, pixels)
    }

    @Test
    fun `mark handles a chain of 200,000 objects without overflowing the stack`() {
        val heap = ToyHeap()
        val first = heap.allocate()
        var last = first
        repeat(199_999) {
            val next = heap.allocate()
            heap.link(last, next)
            last = next
        }
        assertThat(heap.mark(listOf(first))).hasSize(200_000)
    }
}

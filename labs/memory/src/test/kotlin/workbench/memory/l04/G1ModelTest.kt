package workbench.memory.l04

import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import workbench.memory.l04.G1Model.MB

class G1ModelTest {
    private val KB = 1024L
    private val GB = 1024 * MB

    @Test
    fun `region size follows the heap, between 1 MB and 32 MB`() {
        assertThat(G1Model.regionSize(256 * MB)).isEqualTo(1 * MB)
        assertThat(G1Model.regionSize(1 * GB)).isEqualTo(1 * MB)
        assertThat(G1Model.regionSize(3_586_129_920L)).`as`("the 3.4 GB default heap measured on JDK 21").isEqualTo(2 * MB)
        assertThat(G1Model.regionSize(6 * GB)).`as`("6 GB / 2048 = 3 MB, rounded up").isEqualTo(4 * MB)
        assertThat(G1Model.regionSize(8 * GB)).isEqualTo(4 * MB)
        assertThat(G1Model.regionSize(40 * GB)).isEqualTo(32 * MB)
        assertThat(G1Model.regionSize(200 * GB)).isEqualTo(32 * MB)
    }

    @Test
    fun `an object is humongous when it is more than half a region`() {
        assertThat(G1Model.isHumongous(3 * MB, 2 * MB)).isTrue()
        assertThat(G1Model.isHumongous(1 * MB, 2 * MB)).`as`("exactly half").isFalse()
        assertThat(G1Model.isHumongous(1 * MB + 16, 2 * MB)).isTrue()
        assertThat(G1Model.isHumongous(512 * KB, 1 * MB)).isFalse()
        assertThat(G1Model.isHumongous(600 * KB, 1 * MB)).isTrue()
        assertThat(G1Model.isHumongous(8 * MB, 32 * MB)).isFalse()
    }

    @Test
    fun `a humongous object takes whole regions`() {
        assertThat(G1Model.regionsFor(3 * MB, 2 * MB)).isEqualTo(2)
        assertThat(G1Model.regionsFor(4 * MB, 2 * MB)).isEqualTo(2)
        assertThat(G1Model.regionsFor(4 * MB + 1, 2 * MB)).isEqualTo(3)
        assertThat(G1Model.regionsFor(3 * MB, 1 * MB)).isEqualTo(3)
        assertThat(G1Model.regionsFor(3 * MB + 16, 1 * MB)).`as`("a 3 MiB byte[] with its 16-byte header").isEqualTo(4)
    }

    @Test
    fun `a 3 MiB settlement file on a 4 GB heap is humongous and wastes 1 MB`() {
        val region = G1Model.regionSize(4 * GB)
        val file = 3 * MB + 16                                     // byte[3 MiB]: data plus a 16-byte header
        assertThat(region).isEqualTo(2 * MB)
        assertThat(G1Model.isHumongous(file, region)).isTrue()
        assertThat(G1Model.regionsFor(file, region) * region - file).isEqualTo(1 * MB - 16)
    }

    @Test
    fun `mixed collections take at least one eighth of the candidates each`() {
        assertThat(G1Model.minOldRegionsPerMixedGc(0)).isEqualTo(0)
        assertThat(G1Model.minOldRegionsPerMixedGc(1)).isEqualTo(1)
        assertThat(G1Model.minOldRegionsPerMixedGc(8)).isEqualTo(1)
        assertThat(G1Model.minOldRegionsPerMixedGc(9)).isEqualTo(2)
        assertThat(G1Model.minOldRegionsPerMixedGc(100)).isEqualTo(13)
    }

    @Test
    fun `candidates skip mostly live regions and come most garbage first`() {
        val regions = listOf(
            OldRegion(0, 100 * KB),
            OldRegion(1, 950 * KB),              // 93% live: too expensive to copy
            OldRegion(2, 300 * KB),
            OldRegion(3, 1 * MB * 85 / 100),     // exactly 85% live: not below the threshold
            OldRegion(4, 700 * KB),
            OldRegion(5, 10 * KB),
            OldRegion(6, 1_000 * KB),
        )
        // heapBytes = 1 MB allows only 52 KB of waste, so nothing is pruned: this test checks filtering and order
        val candidates = G1Model.mixedCandidates(regions, 1 * MB, heapBytes = 1 * MB)
        assertThat(candidates.map { it.index }).containsExactly(5, 0, 2, 4)
    }

    @Test
    fun `the cheapest candidates are pruned while the garbage left behind stays under 5 percent of the heap`() {
        val regions = listOf(OldRegion(0, 100 * KB), OldRegion(2, 300 * KB), OldRegion(4, 700 * KB), OldRegion(5, 10 * KB))
        // 10 MB heap: up to 524,288 bytes of garbage may be left behind.
        // Region 4 has 324 KB reclaimable: dropped. Region 2 would add 724 KB: kept.
        val candidates = G1Model.mixedCandidates(regions, 1 * MB, heapBytes = 10 * MB)
        assertThat(candidates.map { it.index }).containsExactly(5, 0, 2)
    }

    @Test
    fun `pruning always leaves enough regions to finish in eight mixed collections`() {
        val regions = (0 until 16).map { OldRegion(it, 800 * KB) }           // 16 equal candidates, 224 KB garbage each
        val candidates = G1Model.mixedCandidates(regions, 1 * MB, heapBytes = 4 * GB)
        assertThat(candidates.map { it.index }).containsExactly(0, 1)       // 16 / 8 = 2 must stay
    }

    @Test
    fun `nothing is pruned when each candidate alone is more garbage than the heap may waste`() {
        val regions = (0 until 5).map { OldRegion(it, 500 * KB) }
        val candidates = G1Model.mixedCandidates(regions, 1 * MB, heapBytes = 4 * MB)   // may waste about 205 KB
        assertThat(candidates).hasSize(5)
    }
}

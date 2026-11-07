package workbench.memory.l06

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.within
import org.junit.jupiter.api.Test

/** Every line here is copied from a real JDK 21 run. */
class GcLogTest {

    @Test
    fun `a G1 young pause gives its id, kind, labels, heap numbers and length`() {
        val p = GcLog.parsePause("[0.128s][info][gc] GC(0) Pause Young (Normal) (G1 Evacuation Pause) 14M->1M(256M) 12.723ms")
        assertThat(p).isEqualTo(GcPause(0, "Pause Young", listOf("Normal", "G1 Evacuation Pause"), 14, 1, 256, 12.723))
    }

    @Test
    fun `padded tags and a time decoration change nothing`() {
        val padded = GcLog.parsePause("[0.717s][info][gc          ] GC(3) Pause Young (Normal) (G1 Evacuation Pause) 141M->20M(1024M) 16.335ms")
        assertThat(padded?.millis).isEqualTo(16.335)
        assertThat(padded?.heapCommittedMb).isEqualTo(1024)
        val timed = GcLog.parsePause("[2026-11-07T18:20:06.106+0000][1.331s][info][gc] GC(76) Pause Full (G1 Compaction Pause) 224M->94M(256M) 16.652ms")
        assertThat(timed).isEqualTo(GcPause(76, "Pause Full", listOf("G1 Compaction Pause"), 224, 94, 256, 16.652))
    }

    @Test
    fun `an evacuation failure shows up as a third label`() {
        val p = GcLog.parsePause("[7.885s][info][gc] GC(22) Pause Young (Prepare Mixed) (G1 Evacuation Pause) (Evacuation Failure) 996M->760M(1024M) 43.391ms")
        assertThat(p?.labels).containsExactly("Prepare Mixed", "G1 Evacuation Pause", "Evacuation Failure")
    }

    @Test
    fun `System gc keeps its own parentheses`() {
        val p = GcLog.parsePause("[8.365s][info][gc] GC(24) Pause Full (System.gc()) 974M->1M(1024M) 46.892ms")
        assertThat(p).isEqualTo(GcPause(24, "Pause Full", listOf("System.gc()"), 974, 1, 1024, 46.892))
    }

    @Test
    fun `remark and cleanup are pauses with no labels`() {
        assertThat(GcLog.parsePause("[7.580s][info][gc] GC(21) Pause Remark 583M->583M(1024M) 0.835ms"))
            .isEqualTo(GcPause(21, "Pause Remark", emptyList(), 583, 583, 1024, 0.835))
        assertThat(GcLog.parsePause("[7.604s][info][gc] GC(21) Pause Cleanup 637M->637M(1024M) 0.379ms")?.kind).isEqualTo("Pause Cleanup")
    }

    @Test
    fun `ZGC pauses have a generation prefix and no heap numbers`() {
        assertThat(GcLog.parsePause("[1.279s][info][gc,phases   ] GC(4) y: Pause Mark Start 0.021ms"))
            .isEqualTo(GcPause(4, "Pause Mark Start", emptyList(), null, null, null, 0.021))
        assertThat(GcLog.parsePause("[0.077s][info][gc,phases] GC(0) Y: Pause Mark Start (Major) 0.019ms"))
            .isEqualTo(GcPause(0, "Pause Mark Start", listOf("Major"), null, null, null, 0.019))
        assertThat(GcLog.parsePause("[0.088s][info][gc,phases] GC(0) O: Pause Mark End 0.014ms")?.kind).isEqualTo("Pause Mark End")
    }

    @Test
    fun `Serial, Parallel and Shenandoah pauses parse the same way`() {
        assertThat(GcLog.parsePause("[0.422s][info][gc] GC(0) Pause Young (Allocation Failure) 55M->5M(205M) 13.814ms")?.labels)
            .containsExactly("Allocation Failure")
        assertThat(GcLog.parsePause("[1.542s][info][gc] GC(48) Pause Full (Allocation Failure) 151M->151M(351M) 8.752ms")?.heapAfterMb)
            .isEqualTo(151)
        assertThat(GcLog.parsePause("[0.457s][info][gc] GC(0) Pause Init Mark (unload classes) 0.159ms"))
            .isEqualTo(GcPause(0, "Pause Init Mark", listOf("unload classes"), null, null, null, 0.159))
        assertThat(GcLog.parsePause("[0.479s][info][gc] GC(0) Pause Final Update Refs 0.022ms")?.kind).isEqualTo("Pause Final Update Refs")
    }

    @Test
    fun `lines that are not pauses give null`() {
        listOf(
            "[0.005s][info][gc] Using G1",
            "[0.701s][info][gc,start    ] GC(3) Pause Young (Normal) (G1 Evacuation Pause)",
            "[0.717s][info][gc,phases   ] GC(3)   Evacuate Collection Set: 15.51ms",
            "[7.560s][info][gc] GC(21) Concurrent Mark Cycle",
            "[7.613s][info][gc] GC(21) Concurrent Mark Cycle 53.866ms",
            "[0.042s][info][gc] GC(1) Concurrent Undo Cycle 0.076ms",
            "[1.331s][info][gc] GC(4) Minor Collection (Allocation Rate) 582M(57%)->226M(22%) 0.052s",
            "[1.297s][info][gc,phases   ] GC(4) y: Concurrent Mark 16.749ms",
            "[0.466s][info][gc] GC(0) Concurrent cleanup 260M->133M(263M) 0.066ms",
        ).forEach { assertThat(GcLog.parsePause(it)).`as`(it).isNull() }
    }

    @Test
    fun `a G1 cycle sums to six pauses, one full GC and one evacuation failure`() {
        val log = listOf(
            "[7.552s][info][gc] GC(20) Pause Young (Concurrent Start) (G1 Humongous Allocation) 556M->527M(1024M) 13.734ms",
            "[7.560s][info][gc] GC(21) Concurrent Mark Cycle",
            "[7.580s][info][gc] GC(21) Pause Remark 583M->583M(1024M) 0.835ms",
            "[7.604s][info][gc] GC(21) Pause Cleanup 637M->637M(1024M) 0.379ms",
            "[7.613s][info][gc] GC(21) Concurrent Mark Cycle 53.866ms",
            "[7.885s][info][gc] GC(22) Pause Young (Prepare Mixed) (G1 Evacuation Pause) (Evacuation Failure) 996M->760M(1024M) 43.391ms",
            "[8.054s][info][gc] GC(23) Pause Young (Mixed) (G1 Evacuation Pause) 981M->660M(1024M) 10.429ms",
            "[8.365s][info][gc] GC(24) Pause Full (System.gc()) 974M->1M(1024M) 46.892ms",
        )
        val s = GcLog.summarize(log)
        assertThat(s.pauses).isEqualTo(6)
        assertThat(s.totalMillis).isCloseTo(115.66, within(0.001))
        assertThat(s.longestMillis).isEqualTo(46.892)
        assertThat(s.fullGcs).isEqualTo(1)
        assertThat(s.evacuationFailures).isEqualTo(1)
        assertThat(s.liveAfterLastFullMb).isEqualTo(1)
    }

    @Test
    fun `a ZGC minor collection is three tiny pauses, not 52 ms`() {
        val log = listOf(
            "[1.278s][info][gc] GC(4) Minor Collection (Allocation Rate)",
            "[1.279s][info][gc,phases   ] GC(4) y: Pause Mark Start 0.021ms",
            "[1.297s][info][gc,phases   ] GC(4) y: Concurrent Mark 16.749ms",
            "[1.297s][info][gc,phases   ] GC(4) y: Pause Mark End 0.017ms",
            "[1.305s][info][gc,phases   ] GC(4) y: Pause Relocate Start 0.017ms",
            "[1.331s][info][gc,phases   ] GC(4) y: Concurrent Relocate 24.731ms",
            "[1.331s][info][gc] GC(4) Minor Collection (Allocation Rate) 582M(57%)->226M(22%) 0.052s",
        )
        val s = GcLog.summarize(log)
        assertThat(s.pauses).isEqualTo(3)
        assertThat(s.totalMillis).isCloseTo(0.055, within(0.0001))
        assertThat(s.longestMillis).isEqualTo(0.021)
        assertThat(s.fullGcs).isZero()
        assertThat(s.liveAfterLastFullMb).isNull()
    }
}

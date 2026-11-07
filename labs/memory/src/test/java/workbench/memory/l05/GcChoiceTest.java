package workbench.memory.l05;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static workbench.memory.l05.Collector.*;
import static workbench.memory.l05.Workload.Kind.*;

class GcChoiceTest {
    private static final String UNLOCK = "-XX:+UnlockExperimentalVMOptions";

    @Test
    @DisplayName("JDK 21 to 26 pick G1 only with 2 CPUs and 1,792 MB; otherwise Serial")
    void defaultBeforeJdk27() {
        assertThat(GcChoice.defaultCollector(21, 1, 8_192)).as("1 CPU").isEqualTo(SERIAL);
        assertThat(GcChoice.defaultCollector(21, 2, 1_024)).as("1 GB pod").isEqualTo(SERIAL);
        assertThat(GcChoice.defaultCollector(25, 2, 1_791)).isEqualTo(SERIAL);
        assertThat(GcChoice.defaultCollector(25, 2, 1_792)).isEqualTo(G1);
        assertThat(GcChoice.defaultCollector(25, 4, 8_192)).isEqualTo(G1);
        assertThat(GcChoice.defaultCollector(26, 1, 512)).isEqualTo(SERIAL);
    }

    @Test
    @DisplayName("JDK 27 picks G1 everywhere")
    void defaultFromJdk27() {
        assertThat(GcChoice.defaultCollector(27, 1, 512)).isEqualTo(G1);
        assertThat(GcChoice.defaultCollector(27, 8, 32_768)).isEqualTo(G1);
    }

    @Test
    @DisplayName("Serial, Parallel and G1 take one flag on every JDK")
    void plainFlags() {
        assertThat(GcChoice.flagsFor(SERIAL, 21)).containsExactly("-XX:+UseSerialGC");
        assertThat(GcChoice.flagsFor(PARALLEL, 25)).containsExactly("-XX:+UseParallelGC");
        assertThat(GcChoice.flagsFor(G1, 27)).containsExactly("-XX:+UseG1GC");
        assertThat(GcChoice.flagsFor(SHENANDOAH, 21)).containsExactly("-XX:+UseShenandoahGC");
    }

    @Test
    @DisplayName("generational ZGC needs -XX:+ZGenerational only before JDK 23")
    void zgcFlags() {
        assertThat(GcChoice.flagsFor(ZGC, 21)).containsExactlyInAnyOrder("-XX:+UseZGC", "-XX:+ZGenerational");
        assertThat(GcChoice.flagsFor(ZGC, 23)).containsExactly("-XX:+UseZGC");
        assertThat(GcChoice.flagsFor(ZGC, 25)).containsExactly("-XX:+UseZGC");
    }

    @Test
    @DisplayName("generational Shenandoah: missing before 24, experimental in 24, a product mode from 25")
    void shenandoahGenerationalFlags() {
        assertThatThrownBy(() -> GcChoice.flagsFor(SHENANDOAH_GENERATIONAL, 21)).isInstanceOf(IllegalArgumentException.class);
        List<String> jdk24 = GcChoice.flagsFor(SHENANDOAH_GENERATIONAL, 24);
        assertThat(jdk24).containsExactlyInAnyOrder(UNLOCK, "-XX:+UseShenandoahGC", "-XX:ShenandoahGCMode=generational");
        assertThat(jdk24.indexOf(UNLOCK)).as("unlock first").isLessThan(jdk24.indexOf("-XX:ShenandoahGCMode=generational"));
        assertThat(GcChoice.flagsFor(SHENANDOAH_GENERATIONAL, 25))
                .containsExactlyInAnyOrder("-XX:+UseShenandoahGC", "-XX:ShenandoahGCMode=generational");
    }

    @Test
    @DisplayName("Epsilon always needs the unlock flag, and the unlock flag must come first")
    void epsilonFlags() {
        for (int jdk : new int[] {21, 25, 27}) {
            List<String> flags = GcChoice.flagsFor(EPSILON, jdk);
            assertThat(flags).as("JDK " + jdk).containsExactly(UNLOCK, "-XX:+UseEpsilonGC");
        }
    }

    @Test
    @DisplayName("the decision table: tests, tiny pods, batch jobs, tight pause budgets, everything else")
    void recommend() {
        assertThat(GcChoice.recommend(new Workload(ALLOCATION_TEST, 4, 64, 1_000))).as("allocation budget test").isEqualTo(EPSILON);
        assertThat(GcChoice.recommend(new Workload(SERVICE, 1, 256, 200))).as("1 CPU, 256 MB webhook relay").isEqualTo(SERIAL);
        assertThat(GcChoice.recommend(new Workload(BATCH, 8, 16_384, 5_000))).as("nightly settlement batch").isEqualTo(PARALLEL);
        assertThat(GcChoice.recommend(new Workload(SERVICE, 8, 16_384, 5))).as("fraud scoring with a 5 ms budget").isEqualTo(ZGC);
        assertThat(GcChoice.recommend(new Workload(SERVICE, 2, 4_096, 5))).as("5 ms budget but only 2 CPUs").isEqualTo(G1);
        assertThat(GcChoice.recommend(new Workload(SERVICE, 4, 2_048, 100))).as("ordinary payments API").isEqualTo(G1);
        assertThat(GcChoice.recommend(new Workload(SERVICE, 1, 4_096, 100))).as("1 CPU but a 4 GB heap").isEqualTo(G1);
    }
}

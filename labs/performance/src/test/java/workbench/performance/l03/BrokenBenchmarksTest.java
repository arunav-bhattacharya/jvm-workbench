package workbench.performance.l03;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.openjdk.jmh.annotations.Fork;
import org.openjdk.jmh.annotations.Level;
import org.openjdk.jmh.annotations.Setup;
import org.openjdk.jmh.annotations.Warmup;
import org.openjdk.jmh.infra.Blackhole;

import java.io.IOException;
import java.io.InputStream;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

// The tests inspect the benchmarks with reflection and call them directly. They never time
// anything: timing belongs in a JMH run, not in a unit test.
class BrokenBenchmarksTest {

    private static Method benchmarkMethod(Class<?> type, String name) {
        return Arrays.stream(type.getMethods())
                .filter(m -> m.getName().equals(name))
                .findFirst().orElseThrow(() -> new AssertionError("no public method " + name + " in " + type.getSimpleName()));
    }

    @Test
    @DisplayName("DeadResultBench.seconds hands its result to JMH, by returning it or by using a Blackhole")
    void deadResultIsConsumed() throws Exception {
        Method seconds = benchmarkMethod(DeadResultBench.class, "seconds");
        boolean returns = seconds.getReturnType() != void.class;
        boolean blackhole = Arrays.asList(seconds.getParameterTypes()).contains(Blackhole.class);
        assertThat(returns || blackhole)
                .as("seconds() throws its result away, so the JIT may remove the calculation")
                .isTrue();
        if (returns && seconds.getParameterCount() == 0) {
            assertThat(seconds.invoke(new DeadResultBench())).isEqualTo(ReadingMath.readingSeconds(1_234));
        }
    }

    @Test
    @DisplayName("ConstantInputBench reads its input from a non-final instance field")
    void constantInputIsNotFinal() throws Exception {
        Field words = ConstantInputBench.class.getDeclaredField("words");
        assertThat(Modifier.isStatic(words.getModifiers())).as("words is static").isFalse();
        assertThat(Modifier.isFinal(words.getModifiers()))
                .as("words is final, so javac copies 1234 into seconds() and the JIT can fold the whole call")
                .isFalse();
    }

    @Test
    @DisplayName("ConstantInputBench.seconds follows its input when the field changes")
    void constantInputIsFollowed() throws Exception {
        Field words = ConstantInputBench.class.getDeclaredField("words");
        assertThat(Modifier.isFinal(words.getModifiers())).as("words must not be final").isFalse();
        words.setAccessible(true);
        ConstantInputBench bench = new ConstantInputBench();
        for (long count : new long[] {5_000, 99, 1_000_000}) {
            words.setLong(bench, count);
            assertThat(bench.seconds()).as("seconds() with words = " + count).isEqualTo(ReadingMath.readingSeconds(count));
        }
    }

    @Test
    @DisplayName("ColdBatchBench builds its batch in @Setup, never inside the measured method")
    void coldBatchBuildsOutsideTheMeasurement() throws Exception {
        List<Method> setups = Arrays.stream(ColdBatchBench.class.getMethods())
                .filter(m -> m.isAnnotationPresent(Setup.class)).toList();
        assertThat(setups).as("@Setup methods in ColdBatchBench").isNotEmpty();

        ColdBatchBench bench = new ColdBatchBench();
        for (Method setup : setups) {
            assertThat(setup.getAnnotation(Setup.class).value())
                    .as("Level.Invocation runs setup around every call and distorts short benchmarks")
                    .isNotEqualTo(Level.Invocation);
            setup.invoke(bench);
        }
        long expected = 0;
        for (long words : Fixtures.batch(1_000)) expected += ReadingMath.readingSeconds(words);

        Fixtures.BUILDS.set(0);
        for (int i = 0; i < 50; i++) assertThat(bench.totalSeconds()).isEqualTo(expected);
        assertThat(Fixtures.BUILDS.get()).as("batches built during 50 measured calls").isZero();
    }

    @Test
    @DisplayName("ColdBatchBench warms up for at least 3 iterations and runs in at least one forked JVM")
    void coldBatchWarmsUpAndForks() {
        Warmup warmup = ColdBatchBench.class.getAnnotation(Warmup.class);
        Fork fork = ColdBatchBench.class.getAnnotation(Fork.class);
        // a missing annotation, or a value left blank, means JMH's default: 5 warm-up iterations, 5 forks
        int warmups = warmup == null || warmup.iterations() < 0 ? 5 : warmup.iterations();
        int forks = fork == null || fork.value() < 0 ? 5 : fork.value();
        assertThat(warmups).as("warm-up iterations").isGreaterThanOrEqualTo(3);
        assertThat(forks).as("forks (0 runs the benchmark inside the JVM that launched it)").isGreaterThanOrEqualTo(1);
    }

    @Test
    @DisplayName("all three classes are still benchmarks the JMH annotation processor registered")
    void allRegisteredWithJmh() throws IOException {
        StringBuilder list = new StringBuilder();
        for (URL url : Collections.list(getClass().getClassLoader().getResources("META-INF/BenchmarkList"))) {
            try (InputStream in = url.openStream()) {
                list.append(new String(in.readAllBytes(), StandardCharsets.UTF_8));
            }
        }
        assertThat(list.toString()).contains(
                "workbench.performance.l03.DeadResultBench",
                "workbench.performance.l03.ConstantInputBench",
                "workbench.performance.l03.ColdBatchBench");
    }
}

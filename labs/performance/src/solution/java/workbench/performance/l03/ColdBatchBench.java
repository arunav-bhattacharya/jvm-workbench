package workbench.performance.l03;

import org.openjdk.jmh.annotations.Benchmark;
import org.openjdk.jmh.annotations.BenchmarkMode;
import org.openjdk.jmh.annotations.Fork;
import org.openjdk.jmh.annotations.Level;
import org.openjdk.jmh.annotations.Measurement;
import org.openjdk.jmh.annotations.Mode;
import org.openjdk.jmh.annotations.OutputTimeUnit;
import org.openjdk.jmh.annotations.Scope;
import org.openjdk.jmh.annotations.Setup;
import org.openjdk.jmh.annotations.State;
import org.openjdk.jmh.annotations.Warmup;

import java.util.concurrent.TimeUnit;

@State(Scope.Thread)
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.MICROSECONDS)
@Warmup(iterations = 5, time = 1)        // let the JIT reach C2 before measuring
@Measurement(iterations = 5, time = 1)
@Fork(2)                                 // fresh JVMs: clean profiles, and a second opinion
public class ColdBatchBench {
    int size = 1_000;
    long[] batch;

    @Setup(Level.Trial)                  // runs once per fork, outside the measured time
    public void buildBatch() {
        batch = Fixtures.batch(size);
    }

    @Benchmark
    public long totalFees() {
        long total = 0;
        for (long cents : batch) total += FeeMath.feeCents(cents);
        return total;
    }
}

package workbench.performance.l03;

import org.openjdk.jmh.annotations.Benchmark;
import org.openjdk.jmh.annotations.BenchmarkMode;
import org.openjdk.jmh.annotations.Fork;
import org.openjdk.jmh.annotations.Measurement;
import org.openjdk.jmh.annotations.Mode;
import org.openjdk.jmh.annotations.OutputTimeUnit;
import org.openjdk.jmh.annotations.Scope;
import org.openjdk.jmh.annotations.State;
import org.openjdk.jmh.annotations.Warmup;

import java.util.concurrent.TimeUnit;

/**
 * Broken benchmark 3 of 3. It should measure summing the fees of a 1,000-payment batch.
 * It measures something else, in a JVM that isn't warmed up and isn't fresh.
 * Fix both problems. Keep {@code totalFees()} returning the sum.
 */
@State(Scope.Thread)
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.MICROSECONDS)
@Warmup(iterations = 0)
@Measurement(iterations = 5, time = 1)
@Fork(0)
public class ColdBatchBench {
    int size = 1_000;

    @Benchmark
    public long totalFees() {
        long[] batch = Fixtures.batch(size);
        long total = 0;
        for (long cents : batch) total += FeeMath.feeCents(cents);
        return total;
    }
}

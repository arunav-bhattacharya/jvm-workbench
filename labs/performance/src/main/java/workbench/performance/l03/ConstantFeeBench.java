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
 * Broken benchmark 2 of 3. It returns its result, and it still measures almost nothing.
 * Make the input something neither javac nor the JIT can know in advance.
 * Keep the field name: the test sets it to other amounts.
 */
@State(Scope.Thread)
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.NANOSECONDS)
@Warmup(iterations = 5, time = 1)
@Measurement(iterations = 5, time = 1)
@Fork(2)
public class ConstantFeeBench {
    private final long amountCents = 123_456;   // your IDE suggests final here

    @Benchmark
    public long fee() {
        return FeeMath.feeCents(amountCents);
    }
}

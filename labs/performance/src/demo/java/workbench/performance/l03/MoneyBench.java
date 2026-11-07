package workbench.performance.l03;

import org.openjdk.jmh.annotations.Benchmark;
import org.openjdk.jmh.annotations.BenchmarkMode;
import org.openjdk.jmh.annotations.Fork;
import org.openjdk.jmh.annotations.Measurement;
import org.openjdk.jmh.annotations.Mode;
import org.openjdk.jmh.annotations.OutputTimeUnit;
import org.openjdk.jmh.annotations.Scope;
import org.openjdk.jmh.annotations.Setup;
import org.openjdk.jmh.annotations.State;
import org.openjdk.jmh.annotations.Warmup;
import org.openjdk.jmh.profile.GCProfiler;
import org.openjdk.jmh.results.RunResult;
import org.openjdk.jmh.runner.Runner;
import org.openjdk.jmh.runner.options.OptionsBuilder;
import org.openjdk.jmh.runner.options.VerboseMode;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.concurrent.TimeUnit;

/** Fees for 100 card payments: BigDecimal against long cents, with JMH's GC profiler on. */
@State(Scope.Thread)
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.NANOSECONDS)
@Warmup(iterations = 2, time = 300, timeUnit = TimeUnit.MILLISECONDS)
@Measurement(iterations = 3, time = 300, timeUnit = TimeUnit.MILLISECONDS)
@Fork(1)
public class MoneyBench {
    BigDecimal[] amounts;
    long[] cents;

    @Setup
    public void setup() {                       // built once per fork, outside the measurement
        amounts = new BigDecimal[100];
        cents = new long[100];
        for (int i = 0; i < 100; i++) {
            cents[i] = 1_999 + i;
            amounts[i] = BigDecimal.valueOf(cents[i], 2);
        }
    }

    @Benchmark
    public BigDecimal feeBigDecimal() {         // correct for money, and every operation allocates
        BigDecimal total = BigDecimal.ZERO;
        for (BigDecimal a : amounts) {
            // a new rate object per line, as plenty of real fee code does
            total = total.add(a.multiply(new BigDecimal("0.029")).setScale(2, RoundingMode.HALF_EVEN));
        }
        return total;
    }

    @Benchmark
    public long feeLongCents() {                // 2.9% in integer cents, rounded half up
        long total = 0;
        for (long c : cents) total += (c * 29 + 500) / 1000;
        return total;
    }

    public static void main(String[] args) throws Exception {
        var options = new OptionsBuilder()
                .include(MoneyBench.class.getName())
                .addProfiler(GCProfiler.class)      // the same as -prof gc on the command line
                .verbosity(VerboseMode.SILENT)
                .build();
        System.out.printf("%-14s %12s %10s %14s %8s%n", "Benchmark", "ns/op", "error", "B/op", "error");
        for (RunResult r : new Runner(options).run()) {
            var time = r.getPrimaryResult();
            var bytes = r.getSecondaryResults().get("gc.alloc.rate.norm");
            System.out.printf("%-14s %12.1f %10.1f %14.3f %8.3f%n", r.getParams().getBenchmark().replaceAll(".*\\.", ""),
                    time.getScore(), time.getScoreError(), bytes.getScore(), bytes.getScoreError());
        }
    }
}

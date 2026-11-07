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
import org.openjdk.jmh.infra.Blackhole;
import org.openjdk.jmh.results.RunResult;
import org.openjdk.jmh.runner.Runner;
import org.openjdk.jmh.runner.options.OptionsBuilder;
import org.openjdk.jmh.runner.options.VerboseMode;

import java.util.concurrent.TimeUnit;

/** The same Math.sqrt measured five ways. The iterations are far shorter than JMH's defaults, so treat the numbers as rough. */
@State(Scope.Thread)
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.NANOSECONDS)
@Warmup(iterations = 2, time = 100, timeUnit = TimeUnit.MILLISECONDS)
@Measurement(iterations = 3, time = 100, timeUnit = TimeUnit.MILLISECONDS)
@Fork(1)
public class TrapsBench {
    double x = 2.0;                        // input from a non-final @State field
    static final double CONSTANT = 2.0;    // input the JIT knows at compile time

    @Benchmark
    public void baseline() { }                                // the harness on its own

    @Benchmark
    public void sqrtDiscarded() { Math.sqrt(x); }             // result thrown away

    @Benchmark
    public double sqrtReturned() { return Math.sqrt(x); }     // JMH consumes the return value

    @Benchmark
    public void sqrtBlackhole(Blackhole bh) { bh.consume(Math.sqrt(x)); }

    @Benchmark
    public double sqrtOfConstant() { return Math.sqrt(CONSTANT); }   // folded before it runs

    public static void main(String[] args) throws Exception {
        var options = new OptionsBuilder()
                .include(TrapsBench.class.getName())
                .verbosity(VerboseMode.SILENT)
                .build();
        System.out.printf("%-16s %10s %10s%n", "Benchmark", "ns/op", "error");
        for (RunResult r : new Runner(options).run()) {
            var s = r.getPrimaryResult();
            System.out.printf("%-16s %10.3f %10.3f%n", r.getParams().getBenchmark().replaceAll(".*\\.", ""),
                    s.getScore(), s.getScoreError());
        }
    }
}

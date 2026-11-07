package workbench.performance.l07;

import org.openjdk.jmh.annotations.Benchmark;
import org.openjdk.jmh.annotations.BenchmarkMode;
import org.openjdk.jmh.annotations.Fork;
import org.openjdk.jmh.annotations.Measurement;
import org.openjdk.jmh.annotations.Mode;
import org.openjdk.jmh.annotations.OutputTimeUnit;
import org.openjdk.jmh.annotations.Scope;
import org.openjdk.jmh.annotations.State;
import org.openjdk.jmh.annotations.Warmup;
import org.openjdk.jmh.profile.GCProfiler;
import org.openjdk.jmh.results.RunResult;
import org.openjdk.jmh.runner.Runner;
import org.openjdk.jmh.runner.options.OptionsBuilder;
import org.openjdk.jmh.runner.options.VerboseMode;

import java.util.concurrent.TimeUnit;

/** The proof: the three fee versions under JMH with the GC profiler. Bytes per call is the number to keep. */
@State(Scope.Thread)
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.NANOSECONDS)
@Warmup(iterations = 3, time = 300, timeUnit = TimeUnit.MILLISECONDS)
@Measurement(iterations = 3, time = 300, timeUnit = TimeUnit.MILLISECONDS)
@Fork(1)
public class FeeBench {
    FeeVariants.Payment payment = new FeeVariants.Payment("pay_123", "EUR", "1234.56", "m_7");   // non-final input

    @Benchmark public long before() { return FeeVariants.feeSlow(payment); }

    @Benchmark public long after1Hoisted() { return FeeVariants.feeHoisted(payment); }

    @Benchmark public long after2NoRegex() { return FeeVariants.feeNoRegex(payment); }

    public static void main(String[] args) throws Exception {
        var options = new OptionsBuilder()
                .include(FeeBench.class.getName())
                .addProfiler(GCProfiler.class)
                .verbosity(VerboseMode.SILENT)
                .build();
        System.out.printf("%-14s %10s %10s %12s %8s%n", "Benchmark", "ns/op", "error", "B/op", "error");
        for (RunResult r : new Runner(options).run()) {
            var time = r.getPrimaryResult();
            var bytes = r.getSecondaryResults().get("gc.alloc.rate.norm");
            System.out.printf("%-14s %10.1f %10.1f %12.3f %8.3f%n", r.getParams().getBenchmark().replaceAll(".*\\.", ""),
                    time.getScore(), time.getScoreError(), bytes.getScore(), bytes.getScoreError());
        }
    }
}

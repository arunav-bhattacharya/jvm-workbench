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

/** The proof: each version of the report step under JMH with the GC profiler. Bytes per call is the number to keep. */
@State(Scope.Thread)
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.NANOSECONDS)
@Warmup(iterations = 5, time = 300, timeUnit = TimeUnit.MILLISECONDS)
@Measurement(iterations = 3, time = 300, timeUnit = TimeUnit.MILLISECONDS)
@Fork(1)
public class ReportBench {
    ReportVariants.Document doc = new ReportVariants.Document("doc-7", "fr",
            "the rain came early and the river rose over the old stone");                   // non-final input

    @Benchmark public long before() { return ReportVariants.slow(doc); }

    @Benchmark public long after1Hoisted() { return ReportVariants.hoisted(doc); }

    @Benchmark public long after2Scanned() { return ReportVariants.scanned(doc); }

    @Benchmark public long after3NoRegex() { return ReportVariants.noRegex(doc); }

    public static void main(String[] args) throws Exception {
        var options = new OptionsBuilder()
                .include(ReportBench.class.getName())
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

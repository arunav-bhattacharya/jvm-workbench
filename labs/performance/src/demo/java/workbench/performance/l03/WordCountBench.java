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

import java.util.concurrent.TimeUnit;

/** Counts the words in 100 lines of text two ways, String.split and a character scan, with JMH's GC profiler on. */
@State(Scope.Thread)
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.NANOSECONDS)
@Warmup(iterations = 2, time = 300, timeUnit = TimeUnit.MILLISECONDS)
@Measurement(iterations = 3, time = 300, timeUnit = TimeUnit.MILLISECONDS)
@Fork(1)
public class WordCountBench {
    String[] lines;

    @Setup
    public void setup() {                       // built once per fork, outside the measurement
        lines = new String[100];
        for (int i = 0; i < 100; i++) lines[i] = "the report counts every word on line number " + i;
    }

    @Benchmark
    public long wordsBySplit() {                // short and clear, and every word becomes a new String
        long total = 0;
        for (String line : lines) total += line.split(" ").length;
        return total;
    }

    @Benchmark
    public long wordsByScan() {                 // walks the characters and counts where words start
        long total = 0;
        for (String line : lines) {
            boolean inWord = false;
            for (int i = 0; i < line.length(); i++) {
                boolean letter = line.charAt(i) != ' ';
                if (letter && !inWord) total++;
                inWord = letter;
            }
        }
        return total;
    }

    public static void main(String[] args) throws Exception {
        var options = new OptionsBuilder()
                .include(WordCountBench.class.getName())
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

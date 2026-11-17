package workbench.performance.l02;

import org.openjdk.jmh.annotations.Benchmark;
import org.openjdk.jmh.annotations.BenchmarkMode;
import org.openjdk.jmh.annotations.Fork;
import org.openjdk.jmh.annotations.Measurement;
import org.openjdk.jmh.annotations.Mode;
import org.openjdk.jmh.annotations.OutputTimeUnit;
import org.openjdk.jmh.annotations.Param;
import org.openjdk.jmh.annotations.Scope;
import org.openjdk.jmh.annotations.Setup;
import org.openjdk.jmh.annotations.State;
import org.openjdk.jmh.annotations.Warmup;
import org.openjdk.jmh.results.RunResult;
import org.openjdk.jmh.runner.Runner;
import org.openjdk.jmh.runner.options.OptionsBuilder;
import org.openjdk.jmh.runner.options.VerboseMode;

import java.util.concurrent.TimeUnit;

/**
 * One call site, fed 1, 2 or 3 receiver types (choose others with -Pargs='1 4'). JMH runs each case in a fresh JVM,
 * so every case starts with a clean type profile. Lesson 3 explains the annotations.
 */
@State(Scope.Thread)
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.NANOSECONDS)
@Warmup(iterations = 2, time = 200, timeUnit = TimeUnit.MILLISECONDS)
@Measurement(iterations = 3, time = 200, timeUnit = TimeUnit.MILLISECONDS)
@Fork(1)
public class MegamorphicBench {
    interface Block { long millis(); }   // how long one block of a document takes to read
    record Paragraph(long words) implements Block { public long millis() { return words * 250; } }
    record Heading(long words) implements Block { public long millis() { return 1_000 + words * 400; } }
    record Quote(long words) implements Block { public long millis() { return words * 300; } }
    record Caption(long words) implements Block { public long millis() { return 500 + words * 200; } }

    @Param({"1", "2", "3"})
    int types;

    Block[] blocks;              // not final, and filled in @Setup: lesson 3 explains why

    @Setup
    public void setup() {
        Block[] kinds = {new Paragraph(42), new Heading(6), new Quote(30), new Caption(12)};
        blocks = new Block[1024];
        for (int i = 0; i < blocks.length; i++) blocks[i] = kinds[i % types];
    }

    @Benchmark
    public long readingMillis() {
        long sum = 0;
        for (Block b : blocks) sum += b.millis();            // the call site under test
        return sum;                                          // returned, so JMH consumes it
    }

    public static void main(String[] args) throws Exception {
        var builder = new OptionsBuilder()
                .include(MegamorphicBench.class.getName())
                .verbosity(VerboseMode.SILENT);
        if (args.length > 0) builder.param("types", args);   // for example -Pargs='1 3 4'
        var options = builder.build();
        System.out.println("types at the call site -> ns per document of 1,024 blocks");
        for (RunResult r : new Runner(options).run()) {
            var s = r.getPrimaryResult();
            System.out.printf("  %s type(s): %8.1f ns  (+/- %.1f)%n",
                    r.getParams().getParam("types"), s.getScore(), s.getScoreError());
        }
    }
}

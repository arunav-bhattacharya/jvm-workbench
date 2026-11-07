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
    interface FeeRule { long fee(long cents); }
    static final class Card implements FeeRule { public long fee(long c) { return c * 29 / 1000 + 30; } }
    static final class Sepa implements FeeRule { public long fee(long c) { return 35; } }
    static final class Wallet implements FeeRule { public long fee(long c) { return c * 15 / 1000 + 10; } }
    static final class Bnpl implements FeeRule { public long fee(long c) { return c * 45 / 1000; } }

    @Param({"1", "2", "3"})
    int types;

    FeeRule[] rules;
    long amountCents = 12_345;   // not final: lesson 3 explains why

    @Setup
    public void setup() {
        FeeRule[] kinds = {new Card(), new Sepa(), new Wallet(), new Bnpl()};
        rules = new FeeRule[1024];
        for (int i = 0; i < rules.length; i++) rules[i] = kinds[i % types];
    }

    @Benchmark
    public long feesForBatch() {
        long sum = 0;
        for (FeeRule r : rules) sum += r.fee(amountCents);   // the call site under test
        return sum;                                          // returned, so JMH consumes it
    }

    public static void main(String[] args) throws Exception {
        var builder = new OptionsBuilder()
                .include(MegamorphicBench.class.getName())
                .verbosity(VerboseMode.SILENT);
        if (args.length > 0) builder.param("types", args);   // for example -Pargs='1 3 4'
        var options = builder.build();
        System.out.println("types at the call site -> ns per batch of 1,024 fees");
        for (RunResult r : new Runner(options).run()) {
            var s = r.getPrimaryResult();
            System.out.printf("  %s type(s): %8.1f ns  (+/- %.1f)%n",
                    r.getParams().getParam("types"), s.getScore(), s.getScoreError());
        }
    }
}

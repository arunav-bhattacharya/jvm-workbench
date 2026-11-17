package workbench.container.l03.demo;

import net.bytebuddy.ByteBuddy;
import net.bytebuddy.implementation.MethodDelegation;
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
import workbench.container.l03.InterceptingHandler;
import workbench.container.l03.Interceptor;
import workbench.container.l03.Invocation;
import workbench.container.l03.SubclassBridge;

import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.util.List;
import java.util.Map;
import java.util.concurrent.TimeUnit;

import static net.bytebuddy.matcher.ElementMatchers.named;

/**
 * One booking-fee calculation, called directly and through the container's three kinds of interception.
 * Every chain holds one interceptor that only calls proceed(), so the numbers are the proxies' own cost,
 * and direct() is the baseline to compare against.
 * Short runs on a shared machine: read the order and the bytes, not the decimals.
 */
@State(Scope.Thread)
@BenchmarkMode(Mode.AverageTime)
@OutputTimeUnit(TimeUnit.NANOSECONDS)
@Warmup(iterations = 2, time = 150, timeUnit = TimeUnit.MILLISECONDS)
@Measurement(iterations = 3, time = 150, timeUnit = TimeUnit.MILLISECONDS)
@Fork(1)
public class ProxyCallBench {
    public interface Prices {
        long feeCents(long priceCents);
    }

    public static class PlainPrices implements Prices {
        @Override
        public long feeCents(long priceCents) { return (priceCents * 29 + 500) / 1000; }
    }

    static final Interceptor PASS = Invocation::proceed;          // does nothing but carry on
    static final List<Interceptor> CHAIN = List.of(PASS);

    /** A copy of the forwarding class RegistryGenerator writes for an intercepted interface. */
    static final class Prices_Proxy implements Prices {
        private final Prices target;

        Prices_Proxy(Prices target) { this.target = target; }

        @Override
        public long feeCents(long p0) {
            return (Long) new Invocation("Prices.feeCents", new Object[] {p0}, CHAIN, () -> target.feeCents(p0)).proceed();
        }
    }

    long price = 12_000;                                         // non-final: the JIT can't fold it
    Prices direct, jdkProxy, byteBuddy, generated;

    @Setup
    public void setup() throws Exception {
        direct = new PlainPrices();
        Method fee = Prices.class.getMethod("feeCents", long.class);
        jdkProxy = (Prices) Proxy.newProxyInstance(Prices.class.getClassLoader(), new Class<?>[] {Prices.class},
                new InterceptingHandler(new PlainPrices(), Map.of(fee, CHAIN)));
        byteBuddy = new ByteBuddy().subclass(PlainPrices.class)
                .method(named("feeCents"))
                .intercept(MethodDelegation.withDefaultConfiguration().filter(named("intercept"))
                        .to(new SubclassBridge(Map.of(PlainPrices.class.getMethod("feeCents", long.class), CHAIN))))
                .make().load(PlainPrices.class.getClassLoader()).getLoaded()
                .getConstructor().newInstance();
        generated = new Prices_Proxy(new PlainPrices());
    }

    @Benchmark public long direct() { return direct.feeCents(price); }
    @Benchmark public long jdkProxy() { return jdkProxy.feeCents(price); }
    @Benchmark public long byteBuddy() { return byteBuddy.feeCents(price); }
    @Benchmark public long generated() { return generated.feeCents(price); }

    public static void main(String[] args) throws Exception {
        var options = new OptionsBuilder()
                .include(ProxyCallBench.class.getName())
                .addProfiler(GCProfiler.class)                    // the same as -prof gc
                .verbosity(VerboseMode.SILENT)
                .build();
        System.out.printf("%-10s %9s %9s %9s%n", "Benchmark", "ns/op", "error", "B/op");
        for (RunResult r : new Runner(options).run()) {
            var time = r.getPrimaryResult();
            var bytes = r.getSecondaryResults().get("gc.alloc.rate.norm");
            System.out.printf("%-10s %9.2f %9.2f %9.1f%n", r.getParams().getBenchmark().replaceAll(".*\\.", ""),
                    time.getScore(), time.getScoreError(), bytes.getScore());
        }
    }
}

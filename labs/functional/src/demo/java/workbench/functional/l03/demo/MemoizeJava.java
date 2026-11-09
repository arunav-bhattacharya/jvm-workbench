package workbench.functional.l03.demo;

import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.function.Function;

/** Java twin of Memoize.kt. */
public class MemoizeJava {

    // A higher-order method that returns a function: same answers as f, but each one computed once.
    static <A, R> Function<A, R> memoize(Function<A, R> f) {
        Map<A, R> cache = new ConcurrentHashMap<>();          // captured: one cache per memoized function
        return a -> cache.computeIfAbsent(a, f);
    }

    // Pure but slow: imagine it scans a large BIN table on every call.
    static int binLookups = 0;
    static String issuerCountry(String bin) {
        binLookups++;
        try { Thread.sleep(50); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        return bin.startsWith("4") ? "NL" : "DE";
    }

    // Impure: the exchange rate moves while the service runs.
    static double eurUsd = 1.08;
    static double fxRate(String pair) { return pair.equals("EURUSD") ? eurUsd : 1.0; }

    public static void main(String[] args) {
        Function<String, String> country = memoize(MemoizeJava::issuerCountry);
        List<String> bins = List.of("424242", "555555", "424242", "424242", "555555");
        long start = System.nanoTime();
        System.out.println(bins.stream().map(country).toList());
        System.out.printf("lookups: %d for %d calls, %d ms%n", binLookups, bins.size(), (System.nanoTime() - start) / 1_000_000);

        Function<String, Double> rate = memoize(MemoizeJava::fxRate);
        System.out.println("EURUSD now:                    " + rate.apply("EURUSD"));
        eurUsd = 1.11;                                        // the market moves
        System.out.println("EURUSD after the market moved: " + rate.apply("EURUSD") + "   (real rate: " + fxRate("EURUSD") + ")");
    }
}

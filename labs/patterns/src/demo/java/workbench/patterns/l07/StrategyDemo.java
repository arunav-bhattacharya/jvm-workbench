package workbench.patterns.l07;

import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Three strategies for one decision: which PSP does the router try first? */
public class StrategyDemo {
    record Quote(String psp, long feeMinor, long p95Millis) {}

    public static void main(String[] args) {
        List<Quote> quotes = List.of(
                new Quote("Northpay", 30, 200),
                new Quote("Adyx", 25, 900),
                new Quote("Kestrel", 30, 120));

        // each value is a complete strategy: no class per algorithm
        Map<String, Comparator<Quote>> policies = new LinkedHashMap<>();
        policies.put("cheapest", Comparator.comparingLong(Quote::feeMinor));
        policies.put("fastest", Comparator.comparingLong(Quote::p95Millis));
        policies.put("cheapest, then fastest",
                Comparator.comparingLong(Quote::feeMinor).thenComparingLong(Quote::p95Millis));

        // sorted() is the context: it owns the algorithm and asks the strategy one question
        policies.forEach((name, order) ->
                System.out.println(name + ": " + quotes.stream().sorted(order).map(Quote::psp).toList()));
    }
}

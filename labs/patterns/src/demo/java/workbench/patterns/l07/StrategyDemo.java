package workbench.patterns.l07;

import java.util.Comparator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** Three strategies for one decision: which courier does the shop ask first? */
public class StrategyDemo {
    record Quote(String courier, long priceCents, long minutes) {}

    public static void main(String[] args) {
        List<Quote> quotes = List.of(
                new Quote("Pedal Post", 450, 30),
                new Quote("Big Blue Vans", 350, 90),
                new Quote("Kestrel", 450, 20));

        // each value is a complete strategy: no class per algorithm
        Map<String, Comparator<Quote>> policies = new LinkedHashMap<>();
        policies.put("cheapest", Comparator.comparingLong(Quote::priceCents));
        policies.put("fastest", Comparator.comparingLong(Quote::minutes));
        policies.put("cheapest, then fastest",
                Comparator.comparingLong(Quote::priceCents).thenComparingLong(Quote::minutes));

        // sorted() is the context: it owns the algorithm and asks the strategy one question
        policies.forEach((name, order) ->
                System.out.println(name + ": " + quotes.stream().sorted(order).map(Quote::courier).toList()));
    }
}

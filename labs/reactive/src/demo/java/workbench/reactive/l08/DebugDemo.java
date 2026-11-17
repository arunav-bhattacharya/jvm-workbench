package workbench.reactive.l08;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.Arrays;

/** Where did it fail? An operator error without help, with checkpoints, and the signals log() shows. */
public class DebugDemo {
    // assembled here, far away from where it is subscribed: the cake has two price rows, the code expects one
    static Mono<Integer> priceRow(String cake) {
        return Flux.just(2400, 2600).single();
    }

    static void show(String title, Mono<Integer> chain) {
        try {
            chain.block();
        } catch (RuntimeException e) {
            boolean mentionsPriceRow = Arrays.stream(e.getStackTrace()).anyMatch(f -> f.getMethodName().equals("priceRow"));
            System.out.println(title);
            System.out.println("   " + e);
            System.out.println("   top frame: " + e.getStackTrace()[0]);
            System.out.println("   any frame in priceRow(), where single() was written? " + mentionsPriceRow);
            for (Throwable s : e.getSuppressed()) {
                s.getMessage().lines()
                        .filter(l -> !l.isBlank() && !l.contains("#block"))
                        .limit(4)
                        .map(l -> l.replace("⇢", "->"))               // Reactor prints an arrow here
                        .forEach(l -> System.out.println("   " + l.strip()));
            }
        }
    }

    public static void main(String[] args) {
        show("1. no help", priceRow("chocolate").map(cents -> cents + 100));
        show("2. checkpoint(\"price-row\")", priceRow("chocolate").checkpoint("price-row").map(cents -> cents + 100));
        show("3. checkpoint(\"price-row\", true)", priceRow("chocolate").checkpoint("price-row", true).map(cents -> cents + 100));

        System.out.println("4. log(\"rows\") between a range and take(2)");
        Flux.range(1, 5).log("rows").take(2).blockLast();
    }
}

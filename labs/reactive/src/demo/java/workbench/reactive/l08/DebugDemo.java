package workbench.reactive.l08;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.Arrays;

/** Where did it fail? An operator error without help, with checkpoints, and the signals log() shows. */
public class DebugDemo {
    // assembled here, far away from where it is subscribed: the merchant has two fee rows, the code expects one
    static Mono<Integer> feeRow(String merchant) {
        return Flux.just(120, 80).single();
    }

    static void show(String title, Mono<Integer> chain) {
        try {
            chain.block();
        } catch (RuntimeException e) {
            boolean mentionsFeeRow = Arrays.stream(e.getStackTrace()).anyMatch(f -> f.getMethodName().equals("feeRow"));
            System.out.println(title);
            System.out.println("   " + e);
            System.out.println("   top frame: " + e.getStackTrace()[0]);
            System.out.println("   any frame in feeRow(), where single() was written? " + mentionsFeeRow);
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
        show("1. no help", feeRow("m-1").map(fee -> fee + 1));
        show("2. checkpoint(\"fee-row\")", feeRow("m-1").checkpoint("fee-row").map(fee -> fee + 1));
        show("3. checkpoint(\"fee-row\", true)", feeRow("m-1").checkpoint("fee-row", true).map(fee -> fee + 1));

        System.out.println("4. log(\"rows\") between a range and take(2)");
        Flux.range(1, 5).log("rows").take(2).blockLast();
    }
}

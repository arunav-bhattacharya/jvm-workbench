package workbench.flows.l06;

import reactor.core.publisher.Flux;

import java.io.IOException;

// Closest Java equivalent of onCompletion: Reactor's doFinally, which gets a signal type instead of a cause.
public class CompletionCausesJava {

    static void quietly(Runnable r) {
        try { r.run(); } catch (RuntimeException ignored) { }
    }

    public static void main(String[] args) {
        System.out.println("== doFinally: how did the Flux end?");
        Flux.just(1, 2).doFinally(s -> System.out.println("  success:            " + s)).blockLast();
        quietly(() -> Flux.concat(Flux.just(1), Flux.<Integer>error(new IOException("provider reset")))
                .doFinally(s -> System.out.println("  upstream failure:   " + s)).blockLast());
        Flux.just(1, 2, 3).doFinally(s -> System.out.println("  above take(1):      " + s))
                .take(1).doFinally(s -> System.out.println("  below take(1):      " + s)).blockLast();

        System.out.println("== terminal operators");
        for (var c : new Object[][] {{"Flux.empty().single()", Flux.empty()}, {"Flux.just(1, 2).single()", Flux.just(1, 2)}}) {
            try {
                System.out.printf("  %-28s %s%n", c[0], ((Flux<?>) c[1]).single().block());
            } catch (RuntimeException e) {
                System.out.printf("  %-28s throws %s: %s%n", c[0], e.getClass().getName(), e.getMessage());
            }
        }
    }
}

// Java equivalent of TakeFirst.kt: Reactor's take(2) stops the source by cancelling its
// subscription after the second item; doFinally runs with signal CANCEL. No exception travels
// through the source here, because Reactor has a cancel() call where Flow can only throw.
package workbench.flows.l02;

import reactor.core.publisher.Flux;

public class TakeFirstJava {
    static Flux<Integer> source(String tag) {
        return Flux.range(1, 5)
            .doOnNext(i -> System.out.println("  [" + tag + "] emit " + i))
            .doFinally(signal -> System.out.println("  [" + tag + "] finally " + signal));
    }

    public static void main(String[] args) {
        System.out.println("take(2):");
        source("take").take(2).doOnNext(v -> System.out.println("  got " + v)).blockLast();

        System.out.println("next(), Reactor's first():");
        System.out.println("  first = " + source("first").next().block());
    }
}

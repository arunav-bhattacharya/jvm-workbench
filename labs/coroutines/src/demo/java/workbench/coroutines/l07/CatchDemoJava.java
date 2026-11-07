// Java equivalent of CatchDemo.kt: onErrorResume only handles errors from above it, like catch,
// and doFinally runs on every way out, like onCompletion. An exception thrown in the subscriber's
// own lambda is not an upstream error: no operator above it gets to "handle" it.
package workbench.coroutines.l07;

import java.io.IOException;
import java.io.UncheckedIOException;
import reactor.core.publisher.Flux;

public class CatchDemoJava {
    public static void main(String[] args) {
        String failIn = args.length > 0 ? args[0] : "upstream"; // or "collector"
        Flux<String> lines = Flux.concat(
            Flux.just("pay-1,4250,EUR", "pay-2,-990,EUR"),
            failIn.equals("upstream")
                ? Flux.error(new UncheckedIOException(new IOException("settlement file truncated")))
                : Flux.just("pay-3,120000,GBP"));
        try {
            lines
                .map(l -> l.substring(0, l.indexOf(',')))
                .doFinally(signal -> System.out.println("doFinally: signal = " + signal))
                .onErrorResume(e -> { System.out.println("onErrorResume: " + e); return Flux.just("ABORTED"); })
                .doOnNext(id -> {
                    System.out.println("consume " + id);
                    if (failIn.equals("collector") && id.equals("pay-2")) throw new IllegalStateException("ledger db down");
                })
                .blockLast();
            System.out.println("blockLast returned normally");
        } catch (RuntimeException e) {
            System.out.println("the caller got: " + e);
        }
    }
}

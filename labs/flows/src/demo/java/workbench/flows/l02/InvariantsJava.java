// Java equivalent of Invariants.kt: Reactor has no context rule. A value pushed from another
// thread runs the subscriber's code on that thread, and nothing complains.
package workbench.flows.l02;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import reactor.core.publisher.Flux;

public class InvariantsJava {
    public static void main(String[] args) {
        ExecutorService io = Executors.newSingleThreadExecutor(r -> new Thread(r, "kitchen-io"));
        Flux<String> pushedFromIo = Flux.create(sink -> io.execute(() -> {
            sink.next("from another thread");
            sink.complete();
        }));
        pushedFromIo
            .doOnNext(v -> System.out.println("subscriber got '" + v + "' on " + Thread.currentThread().getName()))
            .blockLast();
        io.shutdown();
    }
}

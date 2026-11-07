// Java equivalent of FlowOnDemo.kt: Reactor's subscribeOn moves the source to another scheduler,
// and publishOn moves everything after it. Without a publishOn, the subscriber runs on that
// scheduler's thread too, which is the difference from flowOn.
package workbench.coroutines.l07;

import java.util.List;
import reactor.core.publisher.Flux;
import reactor.core.scheduler.Schedulers;

public class FlowOnDemoJava {
    static String thread() { return Thread.currentThread().getName(); }

    public static void main(String[] args) {
        Flux.fromIterable(List.of("pay-1,4250,EUR", "pay-2,-990,EUR"))
            .doOnNext(line -> {
                try { Thread.sleep(50); } catch (InterruptedException e) { Thread.currentThread().interrupt(); } // a blocking file read
                System.out.println("read   on " + thread());
            })
            .map(line -> { System.out.println("parse  on " + thread()); return line.split(","); })
            .subscribeOn(Schedulers.boundedElastic())   // the source and the steps above run there
            .publishOn(Schedulers.single())             // the steps below move to another thread
            .map(f -> { System.out.println("format on " + thread()); return f[0] + ": " + f[1] + " cents"; })
            .doOnNext(s -> System.out.println("save   on " + thread() + "  " + s))
            .blockLast();
    }
}

package workbench.reactive.l06;

import reactor.core.publisher.Flux;
import reactor.core.scheduler.Schedulers;

/** publishOn moves what comes after it. subscribeOn moves the source, wherever you write it. */
public class PublishSubscribeDemo {
    static void where(String step) {
        System.out.printf("  %-22s on %s%n", step, Thread.currentThread().getName());
    }

    public static void main(String[] args) {
        System.out.println("1. publishOn(single) in the middle");
        Flux.range(1, 1)
                .doOnNext(i -> where("source"))
                .publishOn(Schedulers.single())
                .doOnNext(i -> where("after publishOn"))
                .blockLast();

        System.out.println("2. subscribeOn(boundedElastic) written last");
        Flux.range(1, 1)
                .doOnNext(i -> where("source"))
                .publishOn(Schedulers.single())
                .doOnNext(i -> where("after publishOn"))
                .subscribeOn(Schedulers.boundedElastic())
                .blockLast();

        System.out.println("3. two subscribeOn calls");
        Flux.range(1, 1)
                .doOnNext(i -> where("source"))
                .subscribeOn(Schedulers.single())               // nearest to the source: this one wins
                .subscribeOn(Schedulers.boundedElastic())       // only adds a thread hop
                .doOnNext(i -> where("downstream"))
                .blockLast();
    }
}

package workbench.reactive.l07;

import org.reactivestreams.Subscription;
import reactor.core.publisher.BaseSubscriber;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.core.scheduler.Schedulers;

import java.time.Duration;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.function.Function;

/** Demand made visible: the requests that reach the source, for one subscriber and five operators. */
public class DemandDemo {
    public static void main(String[] args) {
        System.out.println("1. a subscriber that asks for 2, then 1 more after each item");
        Flux.range(1, 4)
                .doOnRequest(n -> System.out.println("   request(" + n + ")"))
                .subscribe(new BaseSubscriber<Integer>() {
                    @Override
                    protected void hookOnSubscribe(Subscription s) {
                        request(2);
                    }

                    @Override
                    protected void hookOnNext(Integer item) {
                        System.out.println("   got " + item);
                        request(1);
                    }
                });

        show("2. blockLast() alone", Flux.range(1, 40), f -> f);
        show("3. take(3)", Flux.range(1, 40), f -> f.take(3));
        show("4. limitRate(10)", Flux.range(1, 40), f -> f.limitRate(10));
        show("5. publishOn(single())", Flux.range(1, 600), f -> f.publishOn(Schedulers.single()));
        show("6. flatMap(call, 4)", Flux.range(1, 8),
                f -> f.flatMap(i -> Mono.delay(Duration.ofMillis(10)).thenReturn(i), 4));
    }

    static void show(String title, Flux<Integer> source, Function<Flux<Integer>, Flux<Integer>> operator) {
        List<Long> requests = new CopyOnWriteArrayList<>();
        operator.apply(source.doOnRequest(requests::add)).blockLast();
        System.out.printf("%-24s the source saw %s%n", title, requests);
    }
}

package workbench.flows.l08;

import java.util.ArrayList;
import java.util.List;
import java.util.function.UnaryOperator;
import org.reactivestreams.Subscription;
import reactor.core.publisher.BaseSubscriber;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.core.scheduler.Schedulers;

// Java equivalent: a Java caller consumes Kotlin flows through the Flux faces in LedgerFaces
// (ReactorDemand.kt). It sees only Reactor types. Reactor's own operators decide the demand.
public class ReactorDemandJava {

    static void probe(String label, UnaryOperator<Flux<Integer>> operator) {
        List<String> requests = new ArrayList<>();
        Flux<Integer> source = LedgerFaces.entries()   // 600 entries from a Kotlin flow
                .doOnRequest(n -> requests.add(n == Long.MAX_VALUE ? "MAX" : Long.toString(n)));
        operator.apply(source).blockLast();
        String shown = requests.size() > 6 ? requests.subList(0, 6) + " ... (" + requests.size() + " in all)" : requests.toString();
        System.out.printf("  %-34s requests %s%n", label, shown);
    }

    public static void main(String[] args) {
        System.out.println("== 1. how much Reactor operators ask a Flow-backed Flux for");
        probe("blockLast()", f -> f);
        probe("limitRate(10)", f -> f.limitRate(10));
        probe("publishOn(Schedulers.single())", f -> f.publishOn(Schedulers.single()));
        probe("flatMap(Mono::just)", f -> f.flatMap(Mono::just));

        System.out.println("== 2. request(n) from Java parks the Kotlin flow inside emit");
        List<Integer> returned = new ArrayList<>();
        List<Integer> received = new ArrayList<>();
        BaseSubscriber<Integer> subscriber = new BaseSubscriber<>() {
            @Override protected void hookOnSubscribe(Subscription s) { request(2); }
            @Override protected void hookOnNext(Integer v) { received.add(v); }
        };
        LedgerFaces.entriesTracked(returned).subscribe(subscriber);
        System.out.println("  after request(2): received=" + received + ", emit() returned for " + returned);
        subscriber.request(3);
        System.out.println("  after request(3): received=" + received + ", emit() returned for " + returned);
        subscriber.dispose();
    }
}

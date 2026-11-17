package workbench.flows.l08;

import java.util.ArrayList;
import java.util.List;
import org.reactivestreams.Subscription;
import reactor.core.publisher.BaseSubscriber;
import reactor.core.publisher.Flux;
import reactor.core.publisher.FluxSink;

// Java equivalent: Flux.create takes an OverflowStrategy instead of a buffer size.
// 200 synchronous callbacks arrive while the subscriber has asked for one item.
public class ProbeBurstJava {

    static void burst(String label, FluxSink.OverflowStrategy strategy) {
        List<Integer> got = new ArrayList<>();
        BaseSubscriber<Integer> slow = new BaseSubscriber<>() {
            @Override protected void hookOnSubscribe(Subscription s) { request(1); }
            @Override protected void hookOnNext(Integer v) { got.add(v); }
            @Override protected void hookOnError(Throwable e) { System.out.println("    onError " + e.getClass().getSimpleName()); }
        };
        Flux.<Integer>create(sink -> { for (int i = 0; i < 200; i++) sink.next(i); }, strategy).subscribe(slow);
        slow.request(Long.MAX_VALUE);   // the subscriber catches up
        String shown = got.size() > 6 ? got.size() + " items: " + got.subList(0, 3) + " ... " + got.get(got.size() - 1) : got.toString();
        System.out.println("  " + label + ": subscriber got " + shown);
    }

    public static void main(String[] args) {
        System.out.println("== 1. a burst of 200 callbacks, the subscriber has requested 1");
        burst("BUFFER (the default, unbounded)", FluxSink.OverflowStrategy.BUFFER);
        burst("LATEST", FluxSink.OverflowStrategy.LATEST);
        burst("DROP", FluxSink.OverflowStrategy.DROP);
        burst("ERROR", FluxSink.OverflowStrategy.ERROR);
    }
}

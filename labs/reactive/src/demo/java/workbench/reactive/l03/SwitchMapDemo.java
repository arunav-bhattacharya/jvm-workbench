package workbench.reactive.l03;

import reactor.core.publisher.Flux;

import java.time.Duration;

/** Card number lookup as the user types: each new prefix cancels the lookup for the previous one. */
public class SwitchMapDemo {
    // a lookup that streams up to three suggestions, one every 60 ms
    static Flux<String> suggestions(String prefix) {
        return Flux.interval(Duration.ofMillis(60))
                .map(n -> prefix + "-match" + n)
                .take(3)
                .doOnCancel(() -> System.out.println("  cancelled lookup for " + prefix));
    }

    public static void main(String[] args) {
        Flux<String> typed = Flux.just("41", "4111").delayElements(Duration.ofMillis(100));   // at 100 ms and 200 ms

        var shown = typed
                .switchMap(SwitchMapDemo::suggestions)
                .doOnNext(s -> System.out.println("show " + s))
                .collectList()
                .block();
        System.out.println("all shown: " + shown);
    }
}

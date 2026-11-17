// Java equivalent of ColdFlow.kt: a Reactor Flux is cold too. Nothing runs until you subscribe,
// every subscription starts again, and take(3) cancels the source when it has enough.
package workbench.coroutines.l07;

import java.time.Duration;
import java.util.List;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

public class ColdFlowJava {
    static final List<List<String>> PAGES =
        List.of(List.of("apples", "bananas"), List.of("cherries", "dates"), List.of("figs", "grapes"));

    static Flux<String> aisle(String name) {
        return Flux.range(0, 3)
            .concatMap(page -> Mono.fromCallable(() -> {
                    System.out.println("  fetching page " + page + " of the " + name + " aisle");
                    return PAGES.get(page);
                }).delayElement(Duration.ofMillis(20)), 1)   // prefetch 1: ask for one page at a time
            .flatMapIterable(items -> items);
    }

    public static void main(String[] args) {
        System.out.println("building the flux");
        Flux<String> fruit = aisle("fruit");
        System.out.println("built; nothing fetched yet");

        System.out.println("first subscribe:");
        System.out.println("  got " + fruit.collectList().block());

        System.out.println("second subscribe:");
        System.out.println("  got " + fruit.collectList().block());

        System.out.println("take(3):");
        System.out.println("  got " + fruit.take(3).collectList().block());
    }
}

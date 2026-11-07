// Java equivalent of ReactorBridge.kt, from the Java side: Reactor code using the Kotlin
// functions through their Mono and Flux faces. The Kotlin side is ReactorBridge.kt.
package workbench.coroutines.l11;

import java.util.List;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

public class ReactorBridgeJava {
    public static void main(String[] args) {
        System.out.println("1. the Kotlin Mono is cold, so each subscription asks again:");
        Mono<String> north = ReactorBridgeKt.quoteFor("north");
        System.out.println("  built the Mono; nothing asked yet");
        System.out.println("  block() -> " + north.block());
        System.out.println("  block() again -> " + north.block());

        System.out.println("2. an empty Mono and a default:");
        System.out.println("  " + ReactorBridgeKt.quoteFor("nobody").defaultIfEmpty("no quote: use the default acquirer").block());

        System.out.println("3. zip two Kotlin quotes with Reactor operators:");
        System.out.println("  " + Mono.zip(ReactorBridgeKt.quoteFor("north"), ReactorBridgeKt.quoteFor("east"))
            .map(t -> t.getT1() + " | " + t.getT2()).block());

        System.out.println("4. a Kotlin Flow as a Flux:");
        List<String> ticks = ReactorBridgeKt.tickFlux().map(d -> String.format("%.4f", d)).collectList().block();
        System.out.println("  " + ticks);
    }
}

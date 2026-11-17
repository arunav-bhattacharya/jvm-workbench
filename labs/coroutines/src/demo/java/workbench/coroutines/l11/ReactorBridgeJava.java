// Java equivalent of ReactorBridge.kt, from the Java side: Reactor code using the Kotlin
// functions through their Mono and Flux faces. The Kotlin side is ReactorBridge.kt.
package workbench.coroutines.l11;

import java.util.List;
import reactor.core.publisher.Mono;

public class ReactorBridgeJava {
    public static void main(String[] args) {
        System.out.println("1. the Kotlin Mono is cold, so each subscription looks it up again:");
        Mono<String> soup = ReactorBridgeKt.recipeFor("soup");
        System.out.println("  built the Mono; nothing looked up yet");
        System.out.println("  block() -> " + soup.block());
        System.out.println("  block() again -> " + soup.block());

        System.out.println("2. an empty Mono and a default:");
        System.out.println("  " + ReactorBridgeKt.recipeFor("dragon stew").defaultIfEmpty("no recipe: make toast").block());

        System.out.println("3. zip two Kotlin lookups with Reactor operators:");
        System.out.println("  " + Mono.zip(ReactorBridgeKt.recipeFor("soup"), ReactorBridgeKt.recipeFor("bread"))
            .map(t -> t.getT1() + " | " + t.getT2()).block());

        System.out.println("4. a Kotlin Flow as a Flux:");
        List<String> temps = ReactorBridgeKt.temperatureFlux().map(c -> c + " C").collectList().block();
        System.out.println("  " + temps);
    }
}

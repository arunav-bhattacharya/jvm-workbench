package workbench.functional.l08.demo;

import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import java.util.function.Consumer;
import java.util.function.Supplier;

/** The same core and shell in Java: records for the values, a static method for the pure core. */
public class CoreShellJava {
    record Leftover(String id, String dish, Instant cookedAt) {}

    sealed interface FridgeDecision {}
    record ThrowOut(String id) implements FridgeDecision {}
    record Keep(String id, Duration goodFor) implements FridgeDecision {}

    static final Duration KEEPS_FOR = Duration.ofDays(3);

    /** The core: leftovers older than three days go. Pure: the time is a parameter. */
    static List<FridgeDecision> decideFridge(List<Leftover> leftovers, Instant now) {
        return leftovers.stream().<FridgeDecision>map(l -> {
            Duration age = Duration.between(l.cookedAt(), now);
            return age.compareTo(KEEPS_FOR) >= 0 ? new ThrowOut(l.id()) : new Keep(l.id(), KEEPS_FOR.minus(age));
        }).toList();
    }

    /** The shell: reads, calls the core, carries out the decisions. */
    record FridgeJob(Supplier<List<Leftover>> load, Consumer<String> remind, Clock clock) {
        void run() {
            for (FridgeDecision d : decideFridge(load.get(), clock.instant())) {
                if (d instanceof ThrowOut t) remind.accept(t.id());
            }
        }
    }

    public static void main(String[] args) {
        Instant now = Instant.parse("2026-03-10T09:00:00Z");
        List<Leftover> leftovers = List.of(
                new Leftover("l1", "soup", now.minus(Duration.ofDays(4))),
                new Leftover("l2", "rice", now.minus(Duration.ofHours(30))));
        System.out.println("core, called with plain values:");
        decideFridge(leftovers, now).forEach(d -> System.out.println("  " + d));

        System.out.println("shell, with a fixed clock and a fake phone:");
        new FridgeJob(() -> leftovers, id -> System.out.println("  reminder: throw out leftover " + id), Clock.fixed(now, ZoneOffset.UTC)).run();
    }
}

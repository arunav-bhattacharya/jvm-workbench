package workbench.functional.l08;

import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.util.List;
import java.util.function.Consumer;
import java.util.function.Supplier;

/** The same core and shell in Java: records for the values, a static method for the pure core. */
public class CoreShellJava {
    record PendingAuth(String id, long amountMinor, Instant authorizedAt) {}

    sealed interface VoidDecision {}
    record VoidIt(String authId) implements VoidDecision {}
    record Keep(String authId, Duration expiresIn) implements VoidDecision {}

    static final Duration AUTH_LIFETIME = Duration.ofDays(7);

    /** The core: authorizations older than seven days are voided. Pure: the time is a parameter. */
    static List<VoidDecision> decideVoids(List<PendingAuth> auths, Instant now) {
        return auths.stream().<VoidDecision>map(a -> {
            Duration age = Duration.between(a.authorizedAt(), now);
            return age.compareTo(AUTH_LIFETIME) >= 0 ? new VoidIt(a.id()) : new Keep(a.id(), AUTH_LIFETIME.minus(age));
        }).toList();
    }

    /** The shell: reads, calls the core, carries out the decisions. */
    record VoidJob(Supplier<List<PendingAuth>> load, Consumer<String> voidAuth, Clock clock) {
        void run() {
            for (VoidDecision d : decideVoids(load.get(), clock.instant())) {
                if (d instanceof VoidIt v) voidAuth.accept(v.authId());
            }
        }
    }

    public static void main(String[] args) {
        Instant now = Instant.parse("2026-03-10T09:00:00Z");
        List<PendingAuth> auths = List.of(
                new PendingAuth("a1", 1_999, now.minus(Duration.ofDays(8))),
                new PendingAuth("a2", 4_250, now.minus(Duration.ofHours(30))));
        System.out.println("core, called with plain values:");
        decideVoids(auths, now).forEach(d -> System.out.println("  " + d));

        System.out.println("shell, with a fixed clock and a fake gateway:");
        new VoidJob(() -> auths, id -> System.out.println("  POST /authorizations/" + id + "/void"), Clock.fixed(now, ZoneOffset.UTC)).run();
    }
}

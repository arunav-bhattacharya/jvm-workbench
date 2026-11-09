package workbench.functional.l06;

import java.util.HashSet;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.function.Supplier;
import java.util.stream.Stream;

/** The same four bugs, as close as Java gets. Two of them exist in Java too; one Java's compiler prevents. */
public class ScopeBugsJava {
    enum Status { AUTHORIZED, CAPTURED }

    record Pay(String id, long amountMinor, Status status) {
        Pay withStatus(Status s) { return new Pay(id, amountMinor, s); }
    }

    static class MiniLedger {
        private final Set<String> posted = new HashSet<>();
        /** Returns a ledger entry id, or null when this payment was posted before. */
        String post(Pay p) { return posted.add(p.id()) ? "LE-" + p.id() : null; }
    }

    static String settleCached(Pay cached, MiniLedger ledger, Supplier<Pay> fetch) {
        // Optional.map turns a null result into empty, so orElseGet runs: the same trap as ?.let ?: run
        return Optional.ofNullable(cached).map(ledger::post).orElseGet(() -> {
            System.out.println("    cache miss, fetching from the database");
            return ledger.post(fetch.get());
        });
    }

    static class Fx { long amount; }
    static class Form { long amount; Fx fx = new Fx(); }

    record Shop(String name, String scheduleId) {}
    record Schedule(String name, int rateBps) {}

    public static void main(String[] args) {
        Pay p = new Pay("p1", 1_999, Status.AUTHORIZED);

        System.out.println("1. Optional.map(...).orElseGet(...)");
        MiniLedger ledger = new MiniLedger();
        System.out.println("  first settle:  " + settleCached(p, ledger, () -> p));
        System.out.println("  second settle: " + settleCached(p, ledger, () -> p));

        System.out.println("2. peek drops the block's result, like also");
        Pay captured = Stream.of(p).peek(x -> x.withStatus(Status.CAPTURED)).findFirst().orElseThrow();
        System.out.println("  status after peek { withStatus }: " + captured.status());

        System.out.println("3. double-brace initialization, Java's nested apply");
        Form form = new Form() {{ fx = new Fx() {{ amount = 500; }}; }};
        System.out.println("  form.amount = " + form.amount + ", form.fx.amount = " + form.fx.amount);

        System.out.println("4. Java makes you name both lambda parameters, and refuses to reuse a name");
        Map<String, Shop> shops = Map.of("m-1", new Shop("Acme Books", "eu-std"));
        Map<String, Schedule> schedules = Map.of("eu-std", new Schedule("standard-eu", 290));
        String label = Optional.ofNullable(shops.get("m-1"))
                .flatMap(shop -> Optional.ofNullable(schedules.get(shop.scheduleId()))
                        .map(schedule -> shop.name() + ": " + schedule.rateBps() + " bps"))
                .orElse(null);
        System.out.println("  label: " + label);
    }
}

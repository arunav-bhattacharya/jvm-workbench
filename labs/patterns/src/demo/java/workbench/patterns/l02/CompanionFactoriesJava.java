package workbench.patterns.l02;

import java.util.List;

/** The Java twin of CompanionFactories.kt: static factories, a cached instance, and a sealed result. */
public class CompanionFactoriesJava {

    static final class Slot {
        private static final List<String> DAYS = List.of("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN");
        final String day;
        final int hour;
        private Slot(String day, int hour) { this.day = day; this.hour = hour; }
        @Override public String toString() { return day + " " + hour + ":00"; }

        // 1. a named static factory: Slot.parse("SAT 10")
        static SlotResult parse(String raw) {
            String[] parts = raw.trim().split(" ", 2);
            String day = parts[0].toUpperCase();
            int hour;
            try {
                hour = parts.length == 2 ? Integer.parseInt(parts[1].trim()) : -1;
            } catch (NumberFormatException e) {
                hour = -1;
            }
            if (!DAYS.contains(day)) return new BadDay(day);
            if (hour < 8 || hour > 19) return new BadHour(hour);
            return new Ok(new Slot(day, hour));
        }
    }

    sealed interface SlotResult {}                     // permitted subtypes: the records in this file
    record Ok(Slot slot) implements SlotResult {}
    record BadDay(String text) implements SlotResult {}
    record BadHour(int hour) implements SlotResult {}

    static final class Fee {
        private static final Fee STANDARD = new Fee(250);
        final int cents;
        private Fee(int cents) { this.cents = cents; }
        // 2. Java has no operator invoke, so the cached-instance factory needs a name
        static Fee of(int cents) { return cents == 250 ? STANDARD : new Fee(cents); }
    }

    interface OrderBook {
        void record(String entry);
        // 3. a static factory on the interface returns a hidden implementation
        static OrderBook create() { return entry -> System.out.println("  order book <- " + entry); }
    }

    static String describe(SlotResult r) {
        return switch (r) {                               // no default: the compiler checks every case is here
            case Ok ok -> "ok: " + ok.slot();
            case BadDay b -> "no such day '" + b.text() + "'";
            case BadHour h -> "we deliver from 8 to 19, not at " + h.hour();
        };
    }

    public static void main(String[] args) {
        for (String raw : List.of("sat 10", "FRI 23", "MOON 9")) {
            System.out.println("parse(\"" + raw + "\") -> " + describe(Slot.parse(raw)));
        }
        System.out.println("Fee.of(250) == Fee.of(250)? " + (Fee.of(250) == Fee.of(250)));
        System.out.println("Fee.of(400) == Fee.of(400)? " + (Fee.of(400) == Fee.of(400)));
        OrderBook.create().record("o-17 booked for SAT 10:00");
    }
}

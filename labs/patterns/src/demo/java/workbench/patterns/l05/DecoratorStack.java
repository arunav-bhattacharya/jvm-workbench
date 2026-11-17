package workbench.patterns.l05;

import java.util.ArrayList;
import java.util.List;

/** Two decorators around a busy courier line. Same pieces, two orders, two different behaviors. */
public class DecoratorStack {
    interface Booker { String book(int grams); }

    // the real line: busy twice, then it books the parcel
    static final class BusyLine implements Booker {
        private int calls;
        public String book(int grams) {
            if (++calls <= 2) throw new IllegalStateException("line busy, try #" + calls);
            return "BB-" + grams;
        }
    }

    // decorator 1: logs every call that passes through it
    record Logging(Booker inner, List<String> log) implements Booker {
        public String book(int grams) {
            log.add("book " + grams);
            return inner.book(grams);
        }
    }

    // decorator 2: tries up to `attempts` times
    record Retrying(Booker inner, int attempts) implements Booker {
        public String book(int grams) {
            RuntimeException last = null;
            for (int i = 1; i <= attempts; i++) {
                try {
                    return inner.book(grams);
                } catch (RuntimeException e) {
                    last = e;
                }
            }
            throw last;
        }
    }

    public static void main(String[] args) {
        List<String> log = new ArrayList<>();
        Booker retryOutside = new Retrying(new Logging(new BusyLine(), log), 3);
        System.out.println("Retrying(Logging(line)): " + retryOutside.book(1_250) + ", log lines: " + log.size());

        log.clear();
        Booker logOutside = new Logging(new Retrying(new BusyLine(), 3), log);
        System.out.println("Logging(Retrying(line)): " + logOutside.book(1_250) + ", log lines: " + log.size());
    }
}

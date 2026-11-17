package workbench.functional.l08.demo;

import java.math.BigDecimal;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/** The same traps in Java: views that change, and BigDecimal.equals inside a record. */
public class ReadOnlyJava {
    record Menu(String id, List<String> dishes) {}
    record Price(String item, BigDecimal amount) {}

    public static void main(String[] args) {
        // 1. a record holding the caller's list sees every later change
        List<String> backing = new ArrayList<>(List.of("soup"));
        Menu menu = new Menu("week-7", backing);
        backing.add("pie");
        System.out.println("1. menu after the caller adds pie: " + menu.dishes());

        // 2. Collections.unmodifiableList is a view too: it blocks writes through it, not changes behind it
        List<String> view = Collections.unmodifiableList(backing);
        backing.add("cake");
        System.out.println("2. unmodifiable view:             " + view);

        // 3. List.copyOf takes a real snapshot (JDK 10+) and rejects writes
        Menu safe = new Menu("week-8", List.copyOf(backing));
        backing.add("tart");
        System.out.println("3. snapshot after another add:    " + safe.dishes());
        try {
            safe.dishes().add("jam");
        } catch (UnsupportedOperationException e) {
            System.out.println("   add: UnsupportedOperationException");
        }

        // 4. BigDecimal.equals compares the scale, and record equals uses it
        System.out.println("4. Price(2.50).equals(Price(2.5)): "
                + new Price("butter", new BigDecimal("2.50")).equals(new Price("butter", new BigDecimal("2.5"))));
        System.out.println("   compareTo says equal: " + (new BigDecimal("2.50").compareTo(new BigDecimal("2.5")) == 0));
    }
}

package workbench.generics.l04.demo;

import java.util.Iterator;
import java.util.List;

/**
 * Java twin of ProducerDemo.kt. Java has no `out` on a declaration, so Source<T> stays invariant
 * and every method that wants "a source of some kind of Payment" says so at the use site: ? extends.
 */
public class ProducerDemoJava {

    record Card(String id, long cents) implements Payment {
        public String getId() { return id; }
        public long getCents() { return cents; }
    }

    interface Source<T> {
        T next();                                  // null when there is nothing left
    }

    static <T> Source<T> listSource(List<T> items) {
        Iterator<T> it = items.iterator();
        return () -> it.hasNext() ? it.next() : null;
    }

    // ? extends Payment: "a Source of Payment or of some subtype". Without it, a Source<Card> would not fit.
    static long totalCents(Source<? extends Payment> source) {
        long sum = 0;
        for (Payment p = source.next(); p != null; p = source.next()) sum += p.getCents();
        return sum;
    }

    public static void main(String[] args) {
        Source<Card> cards = listSource(List.of(new Card("pay_1", 1_200), new Card("pay_2", 350)));
        System.out.println("card total: " + totalCents(cards));

        Source<? extends Object> anything = listSource(List.of("EUR"));
        System.out.println("first of anything: " + anything.next());

        // Wrong move. Uncomment, predict the error, then run.
        // Source<Payment> plain = cards;
    }
}

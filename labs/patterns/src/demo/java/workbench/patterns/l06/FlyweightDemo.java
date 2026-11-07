package workbench.patterns.l06;

import java.util.Currency;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;

/** Four flyweights: three from the JDK, one of our own. `==` asks "the same object?" */
public class FlyweightDemo {

    // our own: one shared instance per merchant category code
    static final class Mcc {
        private static final Map<String, Mcc> POOL = new ConcurrentHashMap<>();
        private static final AtomicInteger BUILT = new AtomicInteger();
        final String code;

        private Mcc(String code) { this.code = code; BUILT.incrementAndGet(); }

        static Mcc of(String code) { return POOL.computeIfAbsent(code, Mcc::new); }
        static int built() { return BUILT.get(); }
    }

    public static void main(String[] args) {
        Integer a = 127, b = 127;
        Integer c = 128, d = 128;
        System.out.println("Integer 127 == 127: " + (a == b));
        System.out.println("Integer 128 == 128: " + (c == d) + "   equals: " + c.equals(d));

        String parsed = new String("5411");                 // a fresh object, like a field parsed from a message
        System.out.println("parsed == \"5411\": " + (parsed == "5411") + "   after intern(): " + (parsed.intern() == "5411"));

        System.out.println("Currency EUR == EUR: " + (Currency.getInstance("EUR") == Currency.getInstance("EUR")));

        Mcc first = Mcc.of("5411"), second = Mcc.of("5411");
        System.out.println("Mcc 5411 == 5411: " + (first == second) + "   instances built: " + Mcc.built());
    }
}

package workbench.patterns.l06;

import java.util.Currency;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;

/** Four flyweights: three from the JDK, one of our own. `==` asks "the same object?" */
public class FlyweightDemo {

    // our own: one shared instance per product code in the shop's catalog
    static final class Product {
        private static final Map<String, Product> POOL = new ConcurrentHashMap<>();
        private static final AtomicInteger BUILT = new AtomicInteger();
        final String code;

        private Product(String code) { this.code = code; BUILT.incrementAndGet(); }

        static Product of(String code) { return POOL.computeIfAbsent(code, Product::new); }
        static int built() { return BUILT.get(); }
    }

    public static void main(String[] args) {
        Integer a = 127, b = 127;
        Integer c = 128, d = 128;
        System.out.println("Integer 127 == 127: " + (a == b));
        System.out.println("Integer 128 == 128: " + (c == d) + "   equals: " + c.equals(d));

        String parsed = new String("T-1001");               // a fresh object, like a code read from an order form
        System.out.println("parsed == \"T-1001\": " + (parsed == "T-1001") + "   after intern(): " + (parsed.intern() == "T-1001"));

        System.out.println("Currency EUR == EUR: " + (Currency.getInstance("EUR") == Currency.getInstance("EUR")));

        Product first = Product.of("T-1001"), second = Product.of("T-1001");
        System.out.println("Product T-1001 == T-1001: " + (first == second) + "   instances built: " + Product.built());
    }
}

package workbench.kotlin.l03.demo;

/**
 * Java twin of LazyDemo.kt. Java has no lazy delegate. For a per-instance lazy field the usual
 * shape is double-checked locking on a volatile field, which is what Kotlin's SYNCHRONIZED mode does.
 */
public class LazyDemoJava {

    static int rateCalls = 0;

    static final class FxQuoteJava {
        private volatile Double eurUsd;              // null means "not computed yet"

        double eurUsd() {
            Double v = eurUsd;
            if (v == null) {
                synchronized (this) {
                    v = eurUsd;
                    if (v == null) {
                        rateCalls++;
                        if (rateCalls == 1) throw new IllegalStateException("rate service timed out");
                        eurUsd = v = 1.0842;
                    }
                }
            }
            return v;
        }
    }

    public static void main(String[] args) {
        FxQuoteJava quote = new FxQuoteJava();
        try {
            quote.eurUsd();
        } catch (IllegalStateException e) {
            System.out.println("first read failed: " + e.getMessage());
        }
        System.out.println("second read: " + quote.eurUsd() + " (initializer ran " + rateCalls + " times)");
        System.out.println("third read:  " + quote.eurUsd() + " (initializer ran " + rateCalls + " times)");

        // the Kotlin class from Java: getEurUsd() calls Lazy.getValue() on every read
        FxQuote kotlinQuote = new FxQuote();
        try {
            kotlinQuote.getEurUsd();
        } catch (IllegalStateException e) {
            System.out.println("Kotlin FxQuote from Java, first read failed: " + e.getMessage());
        }
        System.out.println("Kotlin FxQuote from Java, second read: " + kotlinQuote.getEurUsd());
    }
}

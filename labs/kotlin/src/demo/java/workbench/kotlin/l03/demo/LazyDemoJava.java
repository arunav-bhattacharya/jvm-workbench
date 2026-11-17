package workbench.kotlin.l03.demo;

/**
 * Java twin of LazyDemo.kt. Java has no lazy delegate. For a per-instance lazy field the usual
 * shape is double-checked locking on a volatile field, which is what Kotlin's SYNCHRONIZED mode does.
 */
public class LazyDemoJava {

    static int lookups = 0;

    static final class PaperSpecJava {
        private volatile Double sheetGrams;          // null means "not computed yet"

        double sheetGrams() {
            Double v = sheetGrams;
            if (v == null) {
                synchronized (this) {
                    v = sheetGrams;
                    if (v == null) {
                        lookups++;
                        if (lookups == 1) throw new IllegalStateException("paper catalogue timed out");
                        sheetGrams = v = 4.99;
                    }
                }
            }
            return v;
        }
    }

    public static void main(String[] args) {
        PaperSpecJava spec = new PaperSpecJava();
        try {
            spec.sheetGrams();
        } catch (IllegalStateException e) {
            System.out.println("first read failed: " + e.getMessage());
        }
        System.out.println("second read: " + spec.sheetGrams() + " (initializer ran " + lookups + " times)");
        System.out.println("third read:  " + spec.sheetGrams() + " (initializer ran " + lookups + " times)");

        // the Kotlin class from Java: getSheetGrams() calls Lazy.getValue() on every read
        PaperSpec kotlinSpec = new PaperSpec();
        try {
            kotlinSpec.getSheetGrams();
        } catch (IllegalStateException e) {
            System.out.println("Kotlin PaperSpec from Java, first read failed: " + e.getMessage());
        }
        System.out.println("Kotlin PaperSpec from Java, second read: " + kotlinSpec.getSheetGrams());
    }
}

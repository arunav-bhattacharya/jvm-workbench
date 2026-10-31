package workbench.generics.l02.demo;

/** Java twin of WhereDemo.kt. Two bounds at once, written with &. */
public class WhereDemoJava {

    static <T extends CharSequence & Comparable<T>> String sortedLabel(T a, T b) {
        return a.compareTo(b) < 0
                ? a + " (" + a.length() + ") then " + b + " (" + b.length() + ")"
                : b + " (" + b.length() + ") then " + a + " (" + a.length() + ")";
    }

    // Wrong moves. Uncomment ONE at a time, predict the error, then run.
    // static <T extends Comparable<T> & CharSequence & Number> void tooMany(T t) {}
    // static <T extends Number & Exception> void amountOrError(T t) {}

    public static void main(String[] args) {
        System.out.println(sortedLabel("SEPA", "ACH"));
        System.out.println(sortedLabel(new StringBuilder("iban"), new StringBuilder("bic")));   // compiles? predict first
        // System.out.println(sortedLabel(42, 7));
    }
}

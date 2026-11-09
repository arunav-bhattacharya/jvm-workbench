package workbench.functional.l06;

import java.util.function.Consumer;

/** Java equivalent: a Java lambda can't assign a local variable at all, so the assignment is a plain statement. */
public class ValInitJava {
    record Authorization(String code, long amountMinor) {}

    static Authorization authorize(long amountMinor) { return new Authorization("A-" + amountMinor % 997, amountMinor); }

    public static void main(String[] args) {
        final String code1;
        Authorization auth1 = authorize(1_999);
        code1 = auth1.code();                                   // a statement, outside any lambda
        System.out.println("statement:    " + code1 + " for " + auth1.amountMinor());

        // Uncomment the next two lines and run again. javac rejects any assignment to a local inside a lambda.
        // String code3;
        // Consumer<Authorization> keep = a -> code3 = a.code();
    }
}

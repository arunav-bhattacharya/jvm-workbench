package workbench.bytecode.l03;

import java.util.function.IntBinaryOperator;
import java.util.function.IntUnaryOperator;
import java.util.function.Supplier;

/** Lambdas, a method reference, string concatenation and a record: every one is an invokedynamic. */
public class IndyTour {
    record Fee(String currency, long amountMinor) {}

    static int add(int a, int b) { return a + b; }

    static Supplier<String> greeter() { return () -> "hello"; }        // captures nothing
    static IntUnaryOperator plus(int fee) { return x -> x + fee; }     // captures fee

    public static void main(String[] args) {
        IntBinaryOperator ref = IndyTour::add;
        Class<?> c = ref.getClass();
        System.out.println("method ref: " + ref.applyAsInt(1_250, 30) + ", class " + c.getName());
        System.out.println("hidden: " + c.isHidden() + ", nestmate of IndyTour: " + (c.getNestHost() == IndyTour.class));
        try {
            Class.forName(c.getName());
        } catch (ClassNotFoundException e) {
            System.out.println("Class.forName(its name): ClassNotFoundException");
        }

        System.out.println("captures nothing: same object both times? " + (greeter() == greeter()));
        IntUnaryOperator p30 = plus(30), p45 = plus(45);
        System.out.println("captures fee: same object? " + (p30 == p45) + ", same class? " + (p30.getClass() == p45.getClass()));

        Fee fee = new Fee("EUR", 3_625);
        System.out.println("concat: " + fee.amountMinor() + " " + fee.currency() + ", record: " + fee);
    }
}

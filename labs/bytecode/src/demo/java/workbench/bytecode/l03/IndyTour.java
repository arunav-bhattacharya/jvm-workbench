package workbench.bytecode.l03;

import java.util.function.IntBinaryOperator;
import java.util.function.IntUnaryOperator;
import java.util.function.Supplier;

/** Lambdas, a method reference, string concatenation and a record: every one is an invokedynamic. */
public class IndyTour {
    record Cue(String name, int seconds) {}

    static int add(int a, int b) { return a + b; }

    static Supplier<String> greeter() { return () -> "hello"; }              // captures nothing
    static IntUnaryOperator delay(int extra) { return s -> s + extra; }      // captures extra

    public static void main(String[] args) {
        IntBinaryOperator ref = IndyTour::add;
        Class<?> c = ref.getClass();
        System.out.println("method ref: " + ref.applyAsInt(90, 30) + ", class " + c.getName());
        System.out.println("hidden: " + c.isHidden() + ", nestmate of IndyTour: " + (c.getNestHost() == IndyTour.class));
        try {
            Class.forName(c.getName());
        } catch (ClassNotFoundException e) {
            System.out.println("Class.forName(its name): ClassNotFoundException");
        }

        System.out.println("captures nothing: same object both times? " + (greeter() == greeter()));
        IntUnaryOperator d5 = delay(5), d10 = delay(10);
        System.out.println("captures extra: same object? " + (d5 == d10) + ", same class? " + (d5.getClass() == d10.getClass()));

        Cue cue = new Cue("thunder", 90);
        System.out.println("concat: " + cue.seconds() + " s to " + cue.name() + ", record: " + cue);
    }
}

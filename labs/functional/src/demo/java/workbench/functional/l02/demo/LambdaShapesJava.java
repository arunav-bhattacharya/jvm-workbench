package workbench.functional.l02.demo;

import java.util.function.LongUnaryOperator;

/**
 * Java twin of LambdaShapes.kt. In Java both lambdas and method references go through invokedynamic,
 * so neither leaves a class file behind. Compare the last two lines with the Kotlin version.
 */
public class LambdaShapesJava {

    static long addFee(long cents) { return cents + 30; }

    static LongUnaryOperator nonCapturing() { return c -> c + 30; }               // uses nothing from outside
    static LongUnaryOperator capturing(long feeCents) { return c -> c + feeCents; } // captures feeCents
    static LongUnaryOperator staticRef() { return LambdaShapesJava::addFee; }      // a method reference

    static final class Shop {
        private final long feeCents;
        Shop(long feeCents) { this.feeCents = feeCents; }
        long withFee(long cents) { return cents + feeCents; }
    }

    static LongUnaryOperator boundRef(Shop s) { return s::withFee; }              // bound to one object

    public static void main(String[] args) {
        Shop s = new Shop(30);
        System.out.println("non-capturing lambda: same object every time?  " + (nonCapturing() == nonCapturing()));
        System.out.println("capturing lambda: same object every time?      " + (capturing(30) == capturing(30)));
        System.out.println("capturing lambdas equal with equals?           " + capturing(30).equals(capturing(30)));
        System.out.println("static method ref: same object?                " + (staticRef() == staticRef()));
        System.out.println("bound method ref s::withFee: same object?      " + (boundRef(s) == boundRef(s)));
        System.out.println();
        Class<?> lambda = nonCapturing().getClass();
        Class<?> ref = staticRef().getClass();
        System.out.println("lambda class:     " + lambda.getName() + "  (hidden: " + lambda.isHidden() + ")");
        System.out.println("method ref class: " + ref.getName() + "  (hidden: " + ref.isHidden() + ")");
    }
}

package workbench.functional.l02.demo;

import java.util.function.LongUnaryOperator;

/**
 * Java twin of LambdaShapes.kt. In Java both lambdas and method references go through invokedynamic,
 * so neither leaves a class file behind. Compare the last two lines with the Kotlin version.
 */
public class LambdaShapesJava {

    static long addRest(long minutes) { return minutes + 10; }                     // let it rest 10 minutes

    static LongUnaryOperator nonCapturing() { return m -> m + 10; }                // uses nothing from outside
    static LongUnaryOperator capturing(long extra) { return m -> m + extra; }      // captures extra
    static LongUnaryOperator staticRef() { return LambdaShapesJava::addRest; }     // a method reference

    static final class ColdOven {                                                  // this oven runs a little cold
        private final long extraMinutes;
        ColdOven(long extraMinutes) { this.extraMinutes = extraMinutes; }
        long adjust(long minutes) { return minutes + extraMinutes; }
    }

    static LongUnaryOperator boundRef(ColdOven o) { return o::adjust; }            // bound to one object

    public static void main(String[] args) {
        ColdOven oven = new ColdOven(5);
        System.out.println("non-capturing lambda: same object every time?  " + (nonCapturing() == nonCapturing()));
        System.out.println("capturing lambda: same object every time?      " + (capturing(5) == capturing(5)));
        System.out.println("capturing lambdas equal with equals?           " + capturing(5).equals(capturing(5)));
        System.out.println("static method ref: same object?                " + (staticRef() == staticRef()));
        System.out.println("bound method ref oven::adjust: same object?    " + (boundRef(oven) == boundRef(oven)));
        System.out.println();
        Class<?> lambda = nonCapturing().getClass();
        Class<?> ref = staticRef().getClass();
        System.out.println("lambda class:     " + lambda.getName() + "  (hidden: " + lambda.isHidden() + ")");
        System.out.println("method ref class: " + ref.getName() + "  (hidden: " + ref.isHidden() + ")");
    }
}

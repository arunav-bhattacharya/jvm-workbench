package workbench.bytecode.l03;

import java.lang.invoke.CallSite;
import java.lang.invoke.LambdaMetafactory;
import java.lang.invoke.MethodHandle;
import java.lang.invoke.MethodHandles;
import java.lang.invoke.MethodType;
import java.lang.invoke.StringConcatFactory;
import java.util.function.Function;
import java.util.function.IntBinaryOperator;
import java.util.function.IntUnaryOperator;

import static java.lang.invoke.MethodType.methodType;

public final class HandMadeLambdas {
    private HandMadeLambdas() {}

    static int addMinor(int a, int b) { return a + b; }
    static int addFee(int feeMinor, int amountMinor) { return amountMinor + feeMinor; }

    // a full-power lookup for this class: it may see the package-private implementation methods
    private static final MethodHandles.Lookup LOOKUP = MethodHandles.lookup();

    // linked once, like one invokedynamic call site. Each holds the factory handle (site.getTarget()).
    private static final MethodHandle ADDER_FACTORY = link(
            "applyAsInt",
            methodType(IntBinaryOperator.class),                 // factory type: no captures, returns the interface
            methodType(int.class, int.class, int.class),         // the interface method, erased: applyAsInt(II)I
            findStatic("addMinor", methodType(int.class, int.class, int.class)),
            methodType(int.class, int.class, int.class));        // the interface method as this lambda sees it

    private static final MethodHandle PLUS_FEE_FACTORY = link(
            "applyAsInt",
            methodType(IntUnaryOperator.class, int.class),       // takes the captured fee
            methodType(int.class, int.class),
            findStatic("addFee", methodType(int.class, int.class, int.class)),   // (fee, amount)
            methodType(int.class, int.class));

    private static final MethodHandle LENGTH_FACTORY;
    static {
        try {
            LENGTH_FACTORY = link(
                    "apply",
                    methodType(Function.class),
                    methodType(Object.class, Object.class),          // Function.apply after erasure
                    LOOKUP.findVirtual(String.class, "length", methodType(int.class)),  // (String)int
                    methodType(Integer.class, String.class));        // what the lambda really takes and returns
        } catch (ReflectiveOperationException e) {
            throw new ExceptionInInitializerError(e);
        }
    }

    // a non-capturing lambda: call the factory once and hand out the same object every time
    private static final IntBinaryOperator ADDER = (IntBinaryOperator) invoke(ADDER_FACTORY);
    private static final Function<String, Integer> LENGTH = castFunction(invoke(LENGTH_FACTORY));

    private static final MethodHandle RECEIPT;
    static {
        try {
            CallSite site = StringConcatFactory.makeConcatWithConstants(
                    LOOKUP, "receipt", methodType(String.class, long.class, String.class),
                    "paid \u0001 to \u0001");                         // \u0001 marks each argument
            RECEIPT = site.getTarget();
        } catch (Exception e) {
            throw new ExceptionInInitializerError(e);
        }
    }

    public static IntBinaryOperator adder() {
        return ADDER;
    }

    public static IntUnaryOperator plusFee(int feeMinor) {
        try {
            return (IntUnaryOperator) PLUS_FEE_FACTORY.invokeExact(feeMinor);   // one new object per call
        } catch (Throwable t) {
            throw new IllegalStateException(t);
        }
    }

    public static Function<String, Integer> lengthOf() {
        return LENGTH;
    }

    public static MethodHandle receipt() {
        return RECEIPT;
    }

    private static MethodHandle link(String name, MethodType factoryType, MethodType erased,
                                     MethodHandle impl, MethodType instantiated) {
        try {
            CallSite site = LambdaMetafactory.metafactory(LOOKUP, name, factoryType, erased, impl, instantiated);
            return site.getTarget();
        } catch (Exception e) {
            throw new ExceptionInInitializerError(e);
        }
    }

    private static MethodHandle findStatic(String name, MethodType type) {
        try {
            return LOOKUP.findStatic(HandMadeLambdas.class, name, type);
        } catch (ReflectiveOperationException e) {
            throw new ExceptionInInitializerError(e);
        }
    }

    private static Object invoke(MethodHandle factory) {
        try {
            return factory.invoke();
        } catch (Throwable t) {
            throw new ExceptionInInitializerError(t);
        }
    }

    @SuppressWarnings("unchecked")
    private static Function<String, Integer> castFunction(Object o) {
        return (Function<String, Integer>) o;
    }
}

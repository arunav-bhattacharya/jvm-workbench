package workbench.bytecode.l03;

import java.lang.invoke.MethodHandle;
import java.util.function.Function;
import java.util.function.IntBinaryOperator;
import java.util.function.IntUnaryOperator;

/**
 * Do by hand what javac does for a lambda: call the bootstrap method that an
 * {@code invokedynamic} instruction would call, and keep the {@code CallSite} it returns.
 *
 * <p>Use {@code LambdaMetafactory.metafactory} for the three lambdas and
 * {@code StringConcatFactory.makeConcatWithConstants} for the receipt. Don't write a lambda
 * or a method reference anywhere in this class: the point is to build them yourself.
 *
 * <p>Link each one ONCE (a static field is fine), the way the JVM links one call site once.
 */
public final class HandMadeLambdas {
    private HandMadeLambdas() {}

    // the implementation methods: the bodies javac would have written as lambda$...$0
    static int addMinor(int a, int b) { return a + b; }
    static int addFee(int feeMinor, int amountMinor) { return amountMinor + feeMinor; }  // captured value first

    /** {@code (a, b) -> addMinor(a, b)}. Captures nothing, so every call returns the same object. */
    public static IntBinaryOperator adder() {
        throw new UnsupportedOperationException("TODO: metafactory with implementation addMinor");
    }

    /** {@code amount -> addFee(feeMinor, amount)}. One linked call site, a new object per fee. */
    public static IntUnaryOperator plusFee(int feeMinor) {
        throw new UnsupportedOperationException("TODO: metafactory whose factory type takes the captured int");
    }

    /** {@code String::length} as a {@code Function<String, Integer>}: erased types and boxing. */
    public static Function<String, Integer> lengthOf() {
        throw new UnsupportedOperationException("TODO: metafactory with a findVirtual handle");
    }

    /** A handle of type {@code (long, String) String} that formats {@code "paid <amount> to <merchant>"}. */
    public static MethodHandle receipt() {
        throw new UnsupportedOperationException("TODO: makeConcatWithConstants with a \\u0001 recipe");
    }
}

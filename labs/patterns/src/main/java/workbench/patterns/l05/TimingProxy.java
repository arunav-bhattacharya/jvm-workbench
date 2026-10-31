package workbench.patterns.l05;

import java.util.function.LongSupplier;

/**
 * A timing proxy built with {@link java.lang.reflect.Proxy}: it implements any interface, forwards
 * every call to the real object, and reports how long each call took.
 *
 * <p>Rules for {@link #wrap}:
 * <ul>
 *   <li>Read {@code nanoTime} once before and once after each forwarded call, and report the
 *       difference to the sink as "InterfaceSimpleName.methodName", for example "IssuerClient.authorize".</li>
 *   <li>If the real object throws, report the call with {@code failed = true} and rethrow the
 *       ORIGINAL exception. Callers must never see {@code InvocationTargetException} or
 *       {@code UndeclaredThrowableException}.</li>
 *   <li>Methods declared by {@code Object} ({@code toString}, {@code equals}, {@code hashCode}) are
 *       forwarded to the real object but not reported.</li>
 * </ul>
 */
public final class TimingProxy {
    private TimingProxy() {}

    /** Where the timings go. */
    @FunctionalInterface
    public interface MetricsSink {
        void record(String name, long nanos, boolean failed);
    }

    /** Returns a proxy that implements {@code iface} and times every call to {@code target}. */
    public static <T> T wrap(Class<T> iface, T target, LongSupplier nanoTime, MetricsSink sink) {
        throw new UnsupportedOperationException("TODO: Proxy.newProxyInstance with an InvocationHandler that times and forwards");
    }
}

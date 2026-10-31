package workbench.patterns.l05;

import java.lang.reflect.InvocationHandler;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Proxy;
import java.util.function.LongSupplier;

public final class TimingProxy {
    private TimingProxy() {}

    @FunctionalInterface
    public interface MetricsSink {
        void record(String name, long nanos, boolean failed);
    }

    @SuppressWarnings("unchecked")
    public static <T> T wrap(Class<T> iface, T target, LongSupplier nanoTime, MetricsSink sink) {
        InvocationHandler handler = (proxy, method, args) -> {
            // 1. Object's own methods: forward, don't time
            if (method.getDeclaringClass() == Object.class) {
                return method.invoke(target, args);
            }
            String name = iface.getSimpleName() + "." + method.getName();
            long start = nanoTime.getAsLong();
            try {
                Object result = method.invoke(target, args);                   // 2. forward the call
                sink.record(name, nanoTime.getAsLong() - start, false);
                return result;
            } catch (InvocationTargetException e) {
                sink.record(name, nanoTime.getAsLong() - start, true);
                throw e.getCause();                                            // 3. unwrap: rethrow what the target threw
            }
        };
        return (T) Proxy.newProxyInstance(iface.getClassLoader(), new Class<?>[]{iface}, handler);
    }
}

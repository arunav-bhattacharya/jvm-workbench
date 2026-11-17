package workbench.patterns.l05;

import java.lang.reflect.InvocationHandler;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Proxy;
import java.util.ArrayList;
import java.util.List;

/** Dynamic proxies: a retrying proxy for any interface, and a tracing proxy that shows self-invocation. */
public class RetryingProxyDemo {
    interface CourierLine { String book(String address, int grams); }
    interface Stockroom { void pick(String item); void pickBoth(String first, String second); }

    static <T> T retrying(Class<T> iface, T target, int maxAttempts) {
        InvocationHandler handler = (proxy, method, args) -> {
            Throwable last = null;
            for (int attempt = 1; attempt <= maxAttempts; attempt++) {
                try {
                    return method.invoke(target, args);
                } catch (InvocationTargetException e) {        // unwrap, or callers see a reflective wrapper
                    last = e.getCause();
                }
            }
            throw last;
        };
        return iface.cast(Proxy.newProxyInstance(iface.getClassLoader(), new Class<?>[]{iface}, handler));
    }

    static <T> T tracing(Class<T> iface, T target, List<String> trace) {
        InvocationHandler handler = (proxy, method, args) -> {
            trace.add(method.getName());
            try {
                return method.invoke(target, args);
            } catch (InvocationTargetException e) {
                throw e.getCause();
            }
        };
        return iface.cast(Proxy.newProxyInstance(iface.getClassLoader(), new Class<?>[]{iface}, handler));
    }

    public static void main(String[] args) {
        int[] calls = {0};
        CourierLine busy = (address, grams) -> {
            if (++calls[0] < 3) throw new IllegalStateException("line busy");
            return "BB-" + grams;
        };
        CourierLine line = retrying(CourierLine.class, busy, 3);
        System.out.println("book -> " + line.book("12 Mill Lane", 1_250) + " after " + calls[0] + " target calls");
        System.out.println("proxy class: " + Proxy.isProxyClass(line.getClass()));

        List<String> trace = new ArrayList<>();
        Stockroom real = new Stockroom() {
            public void pick(String item) { }
            public void pickBoth(String first, String second) { pick(first); pick(second); }   // this.pick(): skips the proxy
        };
        tracing(Stockroom.class, real, trace).pickBoth("tea", "jam");
        System.out.println("calls the proxy saw: " + trace);
    }
}

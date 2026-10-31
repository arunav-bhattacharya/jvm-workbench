package workbench.patterns.l05;

import java.lang.reflect.InvocationHandler;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Proxy;
import java.util.ArrayList;
import java.util.List;

/** Dynamic proxies: a retrying proxy for any interface, and a tracing proxy that shows self-invocation. */
public class RetryingProxyDemo {
    interface PspClient { String charge(String token, long amountMinor); }
    interface Ledger { void post(String entry); void postTwice(String entry); }

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
        PspClient flaky = (token, amount) -> {
            if (++calls[0] < 3) throw new IllegalStateException("PSP 503");
            return "ch_" + amount;
        };
        PspClient psp = retrying(PspClient.class, flaky, 3);
        System.out.println("charge -> " + psp.charge("tok_42", 1_250) + " after " + calls[0] + " target calls");
        System.out.println("proxy class: " + Proxy.isProxyClass(psp.getClass()));

        List<String> trace = new ArrayList<>();
        Ledger real = new Ledger() {
            public void post(String entry) { }
            public void postTwice(String entry) { post(entry); post(entry); }   // this.post(): skips the proxy
        };
        tracing(Ledger.class, real, trace).postTwice("fee 3.20");
        System.out.println("calls the proxy saw: " + trace);
    }
}

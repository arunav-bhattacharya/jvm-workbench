package workbench.bytecode.l04;

import java.lang.reflect.InvocationHandler;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.util.ArrayList;
import java.util.List;

/** Who is `this` inside a default method? It decides which inner calls the handler sees. */
public class DefaultMethodsDemo {
    public interface Ledger {
        long balanceMinor(String account);

        default long totalMinor(String a, String b) {   // calls balanceMinor twice, on `this`
            return balanceMinor(a) + balanceMinor(b);
        }
    }

    static class RealLedger implements Ledger {
        public long balanceMinor(String account) { return account.length() * 1_000L; }
    }

    /** Logs every call it sees. Default methods go either to the target or through invokeDefault. */
    static Ledger logging(Ledger target, boolean useInvokeDefault, List<String> log) {
        InvocationHandler h = (proxy, m, args) -> {
            log.add(m.getName());
            if (useInvokeDefault && m.isDefault()) {
                return InvocationHandler.invokeDefault(proxy, m, args);   // the body runs with this = proxy
            }
            try {
                return m.invoke(target, args);                            // the body runs with this = target
            } catch (InvocationTargetException e) {
                throw e.getCause();
            }
        };
        return (Ledger) Proxy.newProxyInstance(Ledger.class.getClassLoader(), new Class<?>[]{Ledger.class}, h);
    }

    public static void main(String[] args) throws Exception {
        List<String> log = new ArrayList<>();
        long t = logging(new RealLedger(), false, log).totalMinor("ops", "fees");
        System.out.println("forward to target: total=" + t + ", handler saw " + log);

        log.clear();
        t = logging(new RealLedger(), true, log).totalMinor("ops", "fees");
        System.out.println("invokeDefault:     total=" + t + ", handler saw " + log);

        // no implementation class at all: the handler answers balanceMinor, the interface supplies totalMinor
        Ledger noTarget = (Ledger) Proxy.newProxyInstance(Ledger.class.getClassLoader(), new Class<?>[]{Ledger.class},
                (proxy, m, a) -> m.isDefault() ? InvocationHandler.invokeDefault(proxy, m, a) : 500L);
        System.out.println("no target:         total=" + noTarget.totalMinor("x", "y"));

        try {
            Method abstractOne = Ledger.class.getMethod("balanceMinor", String.class);
            InvocationHandler.invokeDefault(noTarget, abstractOne, "x");
        } catch (Throwable e) {
            System.out.println("invokeDefault on an abstract method -> " + e.getClass().getSimpleName());
        }
    }
}

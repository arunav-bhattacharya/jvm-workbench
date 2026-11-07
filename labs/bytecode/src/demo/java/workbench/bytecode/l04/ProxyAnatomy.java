package workbench.bytecode.l04;

import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Modifier;
import java.lang.reflect.Proxy;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/** What Proxy.newProxyInstance generates, which calls reach the handler, and how the class is cached. */
public class ProxyAnatomy {
    public interface FxQuotes {
        long quoteMicros(String pair);
        default long spreadMicros(String pair) { return quoteMicros(pair) / 1_000; }
    }

    public interface Audited { String auditId(); }

    public static void main(String[] args) {
        List<String> seen = new ArrayList<>();
        InvocationHandler h = (proxy, m, a) -> {
            seen.add(m.getDeclaringClass().getSimpleName() + "." + m.getName());
            return switch (m.getName()) {
                case "quoteMicros" -> 1_084_250L;
                case "hashCode" -> 42;
                case "equals" -> proxy == a[0];
                case "toString" -> "FxQuotes proxy";
                default -> null;
            };
        };
        ClassLoader app = FxQuotes.class.getClassLoader();
        FxQuotes q = (FxQuotes) Proxy.newProxyInstance(app, new Class<?>[]{FxQuotes.class}, h);

        // 1. the generated class
        Class<?> pc = q.getClass();
        System.out.println("class      " + Modifier.toString(pc.getModifiers()) + " " + pc.getName());
        System.out.println("extends    " + pc.getSuperclass().getName() + ", implements " + Arrays.toString(pc.getInterfaces()));
        System.out.println("module     " + pc.getModule().getName() + ", hidden: " + pc.isHidden());
        System.out.println("fields     " + Arrays.stream(pc.getDeclaredFields()).map(f -> f.getName()).sorted().toList());
        System.out.println("methods    " + Arrays.stream(pc.getDeclaredMethods()).map(m -> m.getName()).sorted().toList());

        // 2. which calls reach the handler
        q.quoteMicros("EURUSD");
        q.toString();
        q.hashCode();
        q.equals(q);
        q.getClass();
        System.out.println("handler saw " + seen);

        // 3. the class is cached per loader and per ordered interface list
        Object again = Proxy.newProxyInstance(app, new Class<?>[]{FxQuotes.class}, (p, m, a) -> 0L);
        Object ab = Proxy.newProxyInstance(app, new Class<?>[]{FxQuotes.class, Audited.class}, h);
        Object ba = Proxy.newProxyInstance(app, new Class<?>[]{Audited.class, FxQuotes.class}, h);
        System.out.println("same class for the same interface: " + (again.getClass() == pc));
        System.out.println("{FxQuotes, Audited} -> " + ab.getClass().getName() + ", {Audited, FxQuotes} -> " + ba.getClass().getName());
    }
}

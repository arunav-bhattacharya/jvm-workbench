package workbench.bytecode.l04;

import java.lang.reflect.InvocationHandler;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.util.ArrayList;
import java.util.List;

/** Who is `this` inside a default method? It decides which inner calls the handler sees. */
public class DefaultMethodsDemo {
    public interface Scenes {
        int minutes(String scene);

        default int total(String a, String b) {   // calls minutes twice, on `this`
            return minutes(a) + minutes(b);
        }
    }

    static class RealScenes implements Scenes {
        public int minutes(String scene) { return scene.length() * 10; }
    }

    /** Logs every call it sees. Default methods go either to the target or through invokeDefault. */
    static Scenes logging(Scenes target, boolean useInvokeDefault, List<String> log) {
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
        return (Scenes) Proxy.newProxyInstance(Scenes.class.getClassLoader(), new Class<?>[]{Scenes.class}, h);
    }

    public static void main(String[] args) throws Exception {
        List<String> log = new ArrayList<>();
        int t = logging(new RealScenes(), false, log).total("prologue", "duel");
        System.out.println("forward to target: total=" + t + ", handler saw " + log);

        log.clear();
        t = logging(new RealScenes(), true, log).total("prologue", "duel");
        System.out.println("invokeDefault:     total=" + t + ", handler saw " + log);

        // no implementation class at all: the handler answers minutes, the interface supplies total
        Scenes noTarget = (Scenes) Proxy.newProxyInstance(Scenes.class.getClassLoader(), new Class<?>[]{Scenes.class},
                (proxy, m, a) -> m.isDefault() ? InvocationHandler.invokeDefault(proxy, m, a) : 5);
        System.out.println("no target:         total=" + noTarget.total("x", "y"));

        try {
            Method abstractOne = Scenes.class.getMethod("minutes", String.class);
            InvocationHandler.invokeDefault(noTarget, abstractOne, "x");
        } catch (Throwable e) {
            System.out.println("invokeDefault on an abstract method -> " + e.getClass().getSimpleName());
        }
    }
}

package workbench.bytecode.l04;

import java.lang.reflect.InvocationHandler;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;
import java.util.function.LongSupplier;

public final class ResilientProxy {
    private ResilientProxy() {}

    public static <T> T wrap(Class<T> iface, T target, RetryPolicy policy, LongSupplier clock, CallRecorder recorder) {
        InvocationHandler handler = new Handler(iface.getSimpleName(), target, policy, clock, recorder);
        // one generated $ProxyN class per (loader, interface list); this call is cheap after the first
        Object proxy = Proxy.newProxyInstance(iface.getClassLoader(), new Class<?>[]{iface}, handler);
        return iface.cast(proxy);
    }

    private record Handler(String ifaceName, Object target, RetryPolicy policy, LongSupplier clock,
                           CallRecorder recorder) implements InvocationHandler {

        @Override
        public Object invoke(Object proxy, Method method, Object[] args) throws Throwable {
            // 1. equals/hashCode/toString arrive here with getDeclaringClass() == Object.class.
            //    Answer them on the proxy: forwarding equals to the target makes proxy.equals(proxy) false.
            if (method.getDeclaringClass() == Object.class) {
                return switch (method.getName()) {
                    case "equals" -> proxy == args[0];
                    case "hashCode" -> System.identityHashCode(proxy);
                    default -> "Resilient[" + target + "]";
                };
            }
            // 2. a default method's body runs with this = proxy, so its inner calls come back here
            //    and are retried one by one. Retrying the shell would repeat calls that already succeeded.
            if (method.isDefault()) {
                return InvocationHandler.invokeDefault(proxy, method, args);
            }
            // 3. retry loop around the target, timed as one call
            String name = ifaceName + "." + method.getName();
            long start = clock.getAsLong();
            int attempts = 0;
            while (true) {
                attempts++;
                try {
                    Object result = method.invoke(target, args);
                    recorder.record(name, attempts, clock.getAsLong() - start, false);
                    return result;
                } catch (InvocationTargetException e) {
                    Throwable cause = e.getCause();                       // the target's own exception
                    if (attempts >= policy.maxAttempts() || !policy.retries(cause)) {
                        recorder.record(name, attempts, clock.getAsLong() - start, true);
                        throw cause;                                      // 4. unwrapped, as the caller expects
                    }
                }
            }
        }
    }
}

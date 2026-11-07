package workbench.bytecode.l04;

import java.util.function.LongSupplier;

/**
 * Wraps any interface in a JDK dynamic proxy that retries and times each call.
 *
 * <p>The handler has four cases, in this order:
 * <ol>
 *   <li>Methods declared by {@code Object} ({@code equals}, {@code hashCode}, {@code toString}):
 *       answer them on the proxy itself. {@code equals} is identity ({@code proxy == other}),
 *       {@code hashCode} is {@code System.identityHashCode(proxy)}, and {@code toString} is
 *       {@code "Resilient[" + target + "]"}. Never retry, record or forward them.</li>
 *   <li>Default methods: run the interface's own body with
 *       {@code InvocationHandler.invokeDefault(proxy, method, args)}, so the calls it makes come
 *       back through the proxy and are retried one by one. Don't retry or record the default
 *       method itself.</li>
 *   <li>Every other method: read {@code clock} once, then call the target up to
 *       {@code policy.maxAttempts()} times. After a failure, try again only if
 *       {@code policy.retries(cause)} and attempts are left.</li>
 *   <li>When the call ends (success or giving up), read {@code clock} once more and call
 *       {@code recorder.record("Iface.method", attempts, end - start, failed)}. Then return the
 *       result, or throw the target's OWN exception: never an {@code InvocationTargetException}
 *       or {@code UndeclaredThrowableException}.</li>
 * </ol>
 */
public final class ResilientProxy {
    private ResilientProxy() {}

    public static <T> T wrap(Class<T> iface, T target, RetryPolicy policy, LongSupplier clock, CallRecorder recorder) {
        throw new UnsupportedOperationException("TODO: Proxy.newProxyInstance with a retrying, timing handler");
    }
}

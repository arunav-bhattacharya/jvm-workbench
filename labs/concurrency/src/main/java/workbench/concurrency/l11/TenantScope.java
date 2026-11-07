package workbench.concurrency.l11;

import java.util.function.Supplier;

/**
 * Carries the current tenant (merchant group) through one request, so deep code can ask
 * {@link #current()} instead of passing it everywhere. Request threads come from a pool and are reused.
 *
 * <p>This version leaks: a request without a tenant runs as whichever tenant the thread served last,
 * the value survives an exception, and a nested {@code runAs} never gives the outer tenant back.
 * Fix {@link #runAs} so that, when it returns or throws, the thread is exactly as it was before the call.
 */
public final class TenantScope {
    private static final ThreadLocal<String> CURRENT = new ThreadLocal<>();

    private TenantScope() {}

    /** The tenant of the work this thread is running, or {@code "none"}. */
    public static String current() {
        String t = CURRENT.get();
        return t == null ? "none" : t;
    }

    /** Runs {@code work} as {@code tenant} ({@code null} means no tenant), then restores the previous tenant. */
    public static <T> T runAs(String tenant, Supplier<T> work) {
        if (tenant != null) CURRENT.set(tenant);    // a request with no tenant keeps the last one
        return work.get();                           // nothing is ever removed or restored
    }
}

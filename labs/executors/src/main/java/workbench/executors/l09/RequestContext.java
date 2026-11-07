package workbench.executors.l09;

/**
 * A tiny stand-in for SLF4J's MDC: the id of the request the current thread is working for.
 * It is a ThreadLocal, so a value set on one thread is invisible on every other thread.
 */
public final class RequestContext {
    private static final ThreadLocal<String> REQUEST_ID = new ThreadLocal<>();

    private RequestContext() {}

    public static void set(String requestId) {
        REQUEST_ID.set(requestId);
    }

    /** The current thread's request id, or null. */
    public static String get() {
        return REQUEST_ID.get();
    }

    public static void clear() {
        REQUEST_ID.remove();
    }
}

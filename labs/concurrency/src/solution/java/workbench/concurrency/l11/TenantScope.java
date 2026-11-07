package workbench.concurrency.l11;

import java.util.function.Supplier;

public final class TenantScope {
    private static final ThreadLocal<String> CURRENT = new ThreadLocal<>();

    private TenantScope() {}

    public static String current() {
        String t = CURRENT.get();
        return t == null ? "none" : t;
    }

    public static <T> T runAs(String tenant, Supplier<T> work) {
        String previous = CURRENT.get();             // 1. remember what this thread had (null if nothing)
        if (tenant == null) CURRENT.remove(); else CURRENT.set(tenant);
        try {
            return work.get();                       // 2. run with exactly this tenant
        } finally {
            if (previous == null) CURRENT.remove();  // 3. put the thread back as it was, even on an exception
            else CURRENT.set(previous);              //    remove() also frees the map entry; set(null) would not
        }
    }
}

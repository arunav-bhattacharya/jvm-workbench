package workbench.vthreads.l04;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.TimeZone;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * Formats the timestamp printed on payment receipts, in UTC: {@code 2026-03-14T09:26:53.589Z}.
 *
 * <p>{@link SimpleDateFormat} is not thread-safe, so this version keeps one per thread in a
 * {@link ThreadLocal}. That worked as a cache on a 200-thread pool. With one virtual thread per
 * request it builds a new formatter for every request. Replace it with something that is built
 * once and safe to share, and keep {@link #formattersBuilt()} honest: count every formatter you build.
 */
public final class ReceiptStamp {
    private static final AtomicInteger BUILT = new AtomicInteger();

    private static final ThreadLocal<SimpleDateFormat> FORMAT = ThreadLocal.withInitial(() -> {
        BUILT.incrementAndGet();
        SimpleDateFormat f = new SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'");
        f.setTimeZone(TimeZone.getTimeZone("UTC"));
        return f;
    });

    private ReceiptStamp() {}

    /** The receipt timestamp for {@code epochMillis}, in UTC with milliseconds. */
    public static String stamp(long epochMillis) {
        return FORMAT.get().format(new Date(epochMillis));
    }

    /** How many formatter objects this class has built so far. */
    public static int formattersBuilt() {
        return BUILT.get();
    }
}

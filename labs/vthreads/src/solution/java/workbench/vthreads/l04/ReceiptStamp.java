package workbench.vthreads.l04;

import java.time.Instant;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.util.concurrent.atomic.AtomicInteger;

public final class ReceiptStamp {
    private static final AtomicInteger BUILT = new AtomicInteger();

    // DateTimeFormatter is immutable and thread-safe: build it once, share it with every thread
    private static final DateTimeFormatter FORMAT = build();

    private static DateTimeFormatter build() {
        BUILT.incrementAndGet();
        return DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'").withZone(ZoneOffset.UTC);
    }

    private ReceiptStamp() {}

    public static String stamp(long epochMillis) {
        return FORMAT.format(Instant.ofEpochMilli(epochMillis));
    }

    public static int formattersBuilt() {
        return BUILT.get();
    }
}

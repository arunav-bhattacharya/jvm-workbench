package workbench.performance.l05;

import java.io.IOException;
import java.nio.file.Path;
import java.util.Map;

/** Answers two questions from a .jfr file, using the {@code workbench.Authorization} events in it. */
public final class AuthReport {
    private AuthReport() { }

    /**
     * Declined authorizations per merchant. Merchants without a decline are left out.
     * Read the file with {@code jdk.jfr.consumer.RecordingFile} and ignore every other event type.
     */
    public static Map<String, Long> declinesByMerchant(Path jfr) throws IOException {
        throw new UnsupportedOperationException("TODO: count workbench.Authorization events with approved == false");
    }

    /** The merchant whose single slowest authorization took the longest (by event duration). */
    public static String slowestMerchant(Path jfr) throws IOException {
        throw new UnsupportedOperationException("TODO: find the event with the longest getDuration()");
    }
}

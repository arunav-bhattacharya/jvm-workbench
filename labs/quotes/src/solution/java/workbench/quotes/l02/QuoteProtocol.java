package workbench.quotes.l02;

import java.util.concurrent.CancellationException;
import java.util.concurrent.CompletionException;
import java.util.regex.Pattern;

/**
 * The wire protocol: one UTF-8 line per request and per reply.
 *
 * <pre>
 * client: 7 LISBON                 server: 7 OK LISBON 12.42 northline
 * client: 8 DUBLIN                 server: 8 STALE DUBLIN 9.80 fjord     (from the cache)
 * client: 9 ATHENS                 server: 9 ERR no quote for ATHENS
 * client: hello                    server: ERR bad request
 * client: QUIT                     server: BYE, then the server closes the connection
 * </pre>
 *
 * The id is the client's: replies can come back in a different order from the requests, so the
 * client matches them by id.
 */
public final class QuoteProtocol {
    /** The longest request line the server reads, without the newline. Longer lines are rejected. */
    public static final int MAX_LINE = 64;
    /** Requests one connection may have waiting for a quote before the server stops reading it. */
    public static final int MAX_IN_FLIGHT = 16;

    private static final Pattern DESTINATION = Pattern.compile("[A-Z]{2,20}");   // a town, in capital letters

    private QuoteProtocol() {}

    public record Request(String id, String destination) {}

    /** {@code "7 LISBON"} becomes {@code Request("7", "LISBON")}; anything else becomes null. */
    public static Request parse(String line) {
        String[] parts = line.trim().split(" +");
        if (parts.length != 2 || !DESTINATION.matcher(parts[1]).matches()) return null;
        return new Request(parts[0], parts[1]);
    }

    public static String ok(String id, Quote q) {
        return id + (q.stale() ? " STALE " : " OK ") + q.destination() + " " + q.price().toPlainString() + " " + q.provider() + "\n";
    }

    public static String error(String id, Throwable e) {
        Throwable cause = e instanceof CompletionException && e.getCause() != null ? e.getCause() : e;   // stages wrap
        String why = cause instanceof CancellationException ? "cancelled"
                : cause.getMessage() != null ? cause.getMessage() : cause.getClass().getSimpleName();
        return id + " ERR " + why + "\n";
    }
}

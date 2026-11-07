package workbench.quotes.l01;

import java.util.concurrent.CancellationException;
import java.util.concurrent.CompletionException;
import java.util.regex.Pattern;

/**
 * The wire protocol: one UTF-8 line per request and per reply.
 *
 * <pre>
 * client: 7 EURUSD                 server: 7 OK EURUSD 1.0842 northbank
 * client: 8 GBPUSD                 server: 8 STALE GBPUSD 1.2710 fjord     (from the cache)
 * client: 9 USDJPY                 server: 9 ERR no quote for USDJPY
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

    private static final Pattern SYMBOL = Pattern.compile("[A-Z]{6}");

    private QuoteProtocol() {}

    public record Request(String id, String symbol) {}

    /** {@code "7 EURUSD"} becomes {@code Request("7", "EURUSD")}; anything else becomes null. */
    public static Request parse(String line) {
        String[] parts = line.trim().split(" +");
        if (parts.length != 2 || !SYMBOL.matcher(parts[1]).matches()) return null;
        return new Request(parts[0], parts[1]);
    }

    public static String ok(String id, Quote q) {
        return id + (q.stale() ? " STALE " : " OK ") + q.symbol() + " " + q.price().toPlainString() + " " + q.provider() + "\n";
    }

    public static String error(String id, Throwable e) {
        Throwable cause = e instanceof CompletionException && e.getCause() != null ? e.getCause() : e;   // stages wrap
        String why = cause instanceof CancellationException ? "cancelled"
                : cause.getMessage() != null ? cause.getMessage() : cause.getClass().getSimpleName();
        return id + " ERR " + why + "\n";
    }
}

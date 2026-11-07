package workbench.nio.l07;

import org.eclipse.jetty.server.Handler;
import org.eclipse.jetty.server.Request;
import org.eclipse.jetty.server.Response;
import org.eclipse.jetty.util.Callback;

import java.util.concurrent.atomic.AtomicInteger;

/**
 * A blocking handler: each request makes a "JDBC call" that takes {@code delayMs}. It extends
 * {@link Handler.Abstract}, so it declares itself BLOCKING and Jetty never runs it on a selector
 * thread in a way that would stall other connections.
 *
 * <p>The counting around {@link #serve} is done for you; the tests use {@link #maxConcurrent()}.
 */
public class LedgerHandler extends Handler.Abstract {
    private final long delayMs;
    private final AtomicInteger inFlight = new AtomicInteger();
    private final AtomicInteger maxInFlight = new AtomicInteger();

    public LedgerHandler(long delayMs) {
        this.delayMs = delayMs;
    }

    /** The most requests that were inside the handler at the same time. */
    public int maxConcurrent() {
        return maxInFlight.get();
    }

    @Override
    public boolean handle(Request request, Response response, Callback callback) throws Exception {
        maxInFlight.accumulateAndGet(inFlight.incrementAndGet(), Math::max);
        try {
            return serve(request, response, callback);
        } finally {
            inFlight.decrementAndGet();
        }
    }

    /**
     * Sleep {@code delayMs} (the "JDBC call"), then write the body
     * {@code "balance=12500 thread=<thread name> virtual=<true|false>\n"} with
     * {@code Content.Sink.write(response, true, body, callback)}, which completes the callback once
     * the bytes are written. Return true: "I handled this request".
     */
    private boolean serve(Request request, Response response, Callback callback) throws Exception {
        throw new UnsupportedOperationException("TODO: sleep, write the body, return true");
    }
}

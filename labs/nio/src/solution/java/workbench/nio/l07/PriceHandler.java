package workbench.nio.l07;

import org.eclipse.jetty.io.Content;
import org.eclipse.jetty.server.Handler;
import org.eclipse.jetty.server.Request;
import org.eclipse.jetty.server.Response;
import org.eclipse.jetty.util.Callback;

import java.util.concurrent.atomic.AtomicInteger;

public class PriceHandler extends Handler.Abstract {
    private final long delayMs;
    private final AtomicInteger inFlight = new AtomicInteger();
    private final AtomicInteger maxInFlight = new AtomicInteger();

    public PriceHandler(long delayMs) {
        this.delayMs = delayMs;
    }

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

    private boolean serve(Request request, Response response, Callback callback) throws Exception {
        if (delayMs > 0) Thread.sleep(delayMs);                     // the "database lookup": blocks this thread
        Thread t = Thread.currentThread();
        String body = "price=1250 thread=" + t.getName() + " virtual=" + t.isVirtual() + "\n";
        Content.Sink.write(response, true, body, callback);         // completes the callback when written
        return true;                                                // we own this request now
    }
}

package workbench.nio.l07;

import org.eclipse.jetty.io.Content;
import org.eclipse.jetty.server.Handler;
import org.eclipse.jetty.server.Request;
import org.eclipse.jetty.server.Response;
import org.eclipse.jetty.util.Callback;

/**
 * A health check: it never blocks, so it should tell Jetty so. Then Jetty may run it directly on
 * the selector thread (Produce-Consume), with no hand-off to another thread.
 *
 * <p>The body is fine. The declaration is not: change the superclass so the handler's invocation
 * type is NON_BLOCKING.
 */
public class StatusHandler extends Handler.Abstract {   // TODO: declare it non-blocking
    @Override
    public boolean handle(Request request, Response response, Callback callback) {
        Thread t = Thread.currentThread();
        Content.Sink.write(response, true, "UP thread=" + t.getName() + " virtual=" + t.isVirtual() + "\n", callback);
        return true;
    }
}

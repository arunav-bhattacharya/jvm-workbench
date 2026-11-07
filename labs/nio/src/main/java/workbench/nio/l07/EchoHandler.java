package workbench.nio.l07;

import org.eclipse.jetty.server.Handler;
import org.eclipse.jetty.server.Request;
import org.eclipse.jetty.server.Response;
import org.eclipse.jetty.util.Callback;

/**
 * An asynchronous, non-blocking handler: it reads the request body without blocking and answers
 * {@code "echo: <body>"}.
 *
 * <p>Use {@code Content.Source.asStringAsync(request, UTF_8)}, which returns a CompletableFuture of the
 * whole body. When it completes, write the answer with
 * {@code Content.Sink.write(response, true, ..., callback)}; if it fails, call
 * {@code Response.writeError(request, response, callback, failure)}. Return true from
 * {@code handle} right away: the response is finished later, when the callback completes.
 */
public class EchoHandler extends Handler.Abstract.NonBlocking {
    @Override
    public boolean handle(Request request, Response response, Callback callback) {
        throw new UnsupportedOperationException("TODO: read the body asynchronously, write \"echo: <body>\"");
    }
}

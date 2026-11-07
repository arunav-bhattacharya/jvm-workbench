package workbench.nio.l07;

import org.eclipse.jetty.io.Content;
import org.eclipse.jetty.server.Handler;
import org.eclipse.jetty.server.Request;
import org.eclipse.jetty.server.Response;
import org.eclipse.jetty.util.Callback;

import static java.nio.charset.StandardCharsets.UTF_8;

public class EchoHandler extends Handler.Abstract.NonBlocking {
    @Override
    public boolean handle(Request request, Response response, Callback callback) {
        Content.Source.asStringAsync(request, UTF_8).whenComplete((body, failure) -> {   // no thread waits for the body
            if (failure != null) {
                Response.writeError(request, response, callback, failure);
                return;
            }
            Content.Sink.write(response, true, "echo: " + body, callback);
        });
        return true;   // handled; the callback completes later
    }
}

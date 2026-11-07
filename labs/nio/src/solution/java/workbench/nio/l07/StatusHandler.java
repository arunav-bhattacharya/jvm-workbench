package workbench.nio.l07;

import org.eclipse.jetty.io.Content;
import org.eclipse.jetty.server.Handler;
import org.eclipse.jetty.server.Request;
import org.eclipse.jetty.server.Response;
import org.eclipse.jetty.util.Callback;

public class StatusHandler extends Handler.Abstract.NonBlocking {   // a promise to Jetty: this never blocks
    @Override
    public boolean handle(Request request, Response response, Callback callback) {
        Thread t = Thread.currentThread();
        Content.Sink.write(response, true, "UP thread=" + t.getName() + " virtual=" + t.isVirtual() + "\n", callback);
        return true;
    }
}

package workbench.nio.l07;

import org.eclipse.jetty.server.Handler;
import org.eclipse.jetty.server.Server;
import org.eclipse.jetty.server.ServerConnector;
import org.eclipse.jetty.util.thread.QueuedThreadPool;
import org.eclipse.jetty.util.thread.ThreadPool;

/** Starts Jetty 12 servers for the tests. */
public final class PaymentServer {
    private PaymentServer() { }

    /**
     * Start a {@link Server} on {@code pool} with one {@link ServerConnector} bound to host
     * 127.0.0.1 and port 0 (any free port), and {@code handler} as the server's handler.
     * Return the started server.
     */
    public static Server start(ThreadPool pool, Handler handler) throws Exception {
        throw new UnsupportedOperationException("TODO: new Server(pool), a ServerConnector on 127.0.0.1:0, setHandler, start");
    }

    /** The port the server's first connector is listening on. */
    public static int port(Server server) {
        return ((ServerConnector) server.getConnectors()[0]).getLocalPort();
    }

    /**
     * A {@link QueuedThreadPool} with {@code maxThreads} platform threads whose BLOCKING tasks run on
     * virtual threads named {@code ledger-vt-N}: use {@code setVirtualThreadsExecutor} with
     * {@code VirtualThreads.getNamedVirtualThreadsExecutor("ledger-vt-")}.
     */
    public static QueuedThreadPool virtualQueuedThreadPool(int maxThreads) {
        throw new UnsupportedOperationException("TODO: QueuedThreadPool + virtual threads executor");
    }
}

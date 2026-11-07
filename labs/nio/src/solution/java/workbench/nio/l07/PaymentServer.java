package workbench.nio.l07;

import org.eclipse.jetty.server.Handler;
import org.eclipse.jetty.server.Server;
import org.eclipse.jetty.server.ServerConnector;
import org.eclipse.jetty.util.VirtualThreads;
import org.eclipse.jetty.util.thread.QueuedThreadPool;
import org.eclipse.jetty.util.thread.ThreadPool;

public final class PaymentServer {
    private PaymentServer() { }

    public static Server start(ThreadPool pool, Handler handler) throws Exception {
        Server server = new Server(pool);                  // one pool for acceptors, selectors and requests
        ServerConnector connector = new ServerConnector(server);   // default acceptors and selectors
        connector.setHost("127.0.0.1");
        connector.setPort(0);
        server.addConnector(connector);
        server.setHandler(handler);
        server.start();
        return server;
    }

    public static int port(Server server) {
        return ((ServerConnector) server.getConnectors()[0]).getLocalPort();
    }

    public static QueuedThreadPool virtualQueuedThreadPool(int maxThreads) {
        QueuedThreadPool pool = new QueuedThreadPool(maxThreads);
        // BLOCKING tasks go to virtual threads; selectors, acceptors and NON_BLOCKING tasks stay on platform threads
        pool.setVirtualThreadsExecutor(VirtualThreads.getNamedVirtualThreadsExecutor("ledger-vt-"));
        return pool;
    }
}

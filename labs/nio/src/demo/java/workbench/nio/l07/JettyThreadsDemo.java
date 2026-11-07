package workbench.nio.l07;

import org.eclipse.jetty.io.Content;
import org.eclipse.jetty.server.Handler;
import org.eclipse.jetty.server.Request;
import org.eclipse.jetty.server.Response;
import org.eclipse.jetty.server.Server;
import org.eclipse.jetty.server.ServerConnector;
import org.eclipse.jetty.util.Callback;
import org.eclipse.jetty.util.VirtualThreads;
import org.eclipse.jetty.util.thread.QueuedThreadPool;
import org.eclipse.jetty.util.thread.ThreadPool;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

/** What does a default Jetty 12 server start, and which thread runs a blocking vs a non-blocking handler? */
public class JettyThreadsDemo {
    static final HttpClient CLIENT = HttpClient.newBuilder().proxy(HttpClient.Builder.NO_PROXY).build();

    static String where() {
        Thread t = Thread.currentThread();
        return t.getName() + " virtual=" + t.isVirtual();
    }

    static class Blocking extends Handler.Abstract {                  // declares BLOCKING
        @Override public boolean handle(Request req, Response res, Callback cb) {
            Content.Sink.write(res, true, where(), cb);
            return true;
        }
    }

    static class NonBlocking extends Handler.Abstract.NonBlocking {   // declares NON_BLOCKING
        @Override public boolean handle(Request req, Response res, Callback cb) {
            Content.Sink.write(res, true, where(), cb);
            return true;
        }
    }

    static Server start(ThreadPool pool, Handler handler) throws Exception {
        Server server = new Server(pool);
        ServerConnector connector = new ServerConnector(server);
        connector.setHost("127.0.0.1");
        connector.setPort(0);
        server.addConnector(connector);
        server.setHandler(handler);
        server.start();
        return server;
    }

    static String get(Server server) throws Exception {
        int port = ((ServerConnector) server.getConnectors()[0]).getLocalPort();
        return CLIENT.send(HttpRequest.newBuilder(URI.create("http://127.0.0.1:" + port + "/")).build(),
                HttpResponse.BodyHandlers.ofString()).body();
    }

    public static void main(String[] args) throws Exception {
        QueuedThreadPool defaults = new QueuedThreadPool();
        Server server = start(defaults, new Blocking());
        ServerConnector c = (ServerConnector) server.getConnectors()[0];
        System.out.println("cpus=" + Runtime.getRuntime().availableProcessors() + " acceptors=" + c.getAcceptors()
                + " selectors=" + c.getSelectorManager().getSelectorCount());
        System.out.println("QueuedThreadPool min=" + defaults.getMinThreads() + " max=" + defaults.getMaxThreads()
                + " started=" + defaults.getThreads() + " leased=" + defaults.getLeasedThreads());
        System.out.println("[platform pool] BLOCKING handler     -> " + get(server));
        server.stop();
        server = start(new QueuedThreadPool(), new NonBlocking());
        System.out.println("[platform pool] NON_BLOCKING handler -> " + get(server));
        server.stop();

        for (boolean blocking : new boolean[] {true, false}) {
            QueuedThreadPool pool = new QueuedThreadPool();
            pool.setVirtualThreadsExecutor(VirtualThreads.getNamedVirtualThreadsExecutor("jetty-vt-"));
            server = start(pool, blocking ? new Blocking() : new NonBlocking());
            System.out.println("[pool + virtual threads] " + (blocking ? "BLOCKING handler     -> " : "NON_BLOCKING handler -> ") + get(server));
            server.stop();
        }
    }
}

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
import org.eclipse.jetty.util.thread.VirtualThreadPool;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

/** 40 concurrent requests to a handler that blocks 300 ms, on three kinds of thread pool. */
public class JettyLoadDemo {
    static final HttpClient CLIENT = HttpClient.newBuilder()
            .proxy(HttpClient.Builder.NO_PROXY).version(HttpClient.Version.HTTP_1_1).build();

    static class SlowLedger extends Handler.Abstract {
        final AtomicInteger inFlight = new AtomicInteger(), max = new AtomicInteger();

        @Override public boolean handle(Request req, Response res, Callback cb) throws Exception {
            max.accumulateAndGet(inFlight.incrementAndGet(), Math::max);
            try {
                Thread.sleep(300);                                  // the "JDBC call"
            } finally {
                inFlight.decrementAndGet();
            }
            Content.Sink.write(res, true, "ok", cb);
            return true;
        }
    }

    static void run(String label, ThreadPool pool) throws Exception {
        SlowLedger ledger = new SlowLedger();
        Server server = new Server(pool);
        ServerConnector connector = new ServerConnector(server);
        connector.setHost("127.0.0.1");
        connector.setPort(0);
        server.addConnector(connector);
        server.setHandler(ledger);
        server.start();
        URI uri = URI.create("http://127.0.0.1:" + connector.getLocalPort() + "/");
        long t0 = System.nanoTime();
        List<CompletableFuture<HttpResponse<String>>> calls = new ArrayList<>();
        for (int i = 0; i < 40; i++) calls.add(CLIENT.sendAsync(HttpRequest.newBuilder(uri).build(), HttpResponse.BodyHandlers.ofString()));
        for (var call : calls) call.get(30, TimeUnit.SECONDS);
        System.out.printf("%-38s 40 x 300 ms -> %,5d ms, at most %d in the handler at once%n",
                label, (System.nanoTime() - t0) / 1_000_000, ledger.max.get());
        server.stop();
    }

    public static void main(String[] args) throws Exception {
        run("QueuedThreadPool(max=12)", new QueuedThreadPool(12));
        QueuedThreadPool withVirtual = new QueuedThreadPool(12);
        withVirtual.setVirtualThreadsExecutor(VirtualThreads.getNamedVirtualThreadsExecutor("jetty-vt-"));
        run("QueuedThreadPool(max=12) + virtual", withVirtual);
        run("VirtualThreadPool(maxThreads=8)", new VirtualThreadPool(8));
    }
}

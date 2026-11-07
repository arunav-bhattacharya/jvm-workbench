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

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.Arrays;
import java.util.List;
import java.util.stream.Collectors;

/** Which execution-strategy mode ran the handler? Read it from the handler's own stack. */
public class StrategyDemo {
    static final HttpClient CLIENT = HttpClient.newBuilder().proxy(HttpClient.Builder.NO_PROXY).build();

    static String mode() {
        List<String> methods = Arrays.stream(Thread.currentThread().getStackTrace())
                .filter(f -> f.getClassName().contains("AdaptiveExecutionStrategy") || f.getClassName().contains("VirtualThread"))
                .map(f -> f.getClassName().replaceAll(".*\\.", "") + "." + f.getMethodName())
                .collect(Collectors.toList());
        String strategy = methods.stream().filter(m -> m.contains("RunTask") && !m.equals("AdaptiveExecutionStrategy.runTask"))
                .findFirst().orElse(methods.isEmpty() ? "no strategy frame: dispatched to the pool" : methods.get(0));
        return Thread.currentThread().getName() + " :: " + strategy;
    }

    static Handler handler(boolean nonBlocking) {
        return nonBlocking
                ? new Handler.Abstract.NonBlocking() {
                    @Override public boolean handle(Request r, Response s, Callback c) { Content.Sink.write(s, true, mode(), c); return true; } }
                : new Handler.Abstract() {
                    @Override public boolean handle(Request r, Response s, Callback c) { Content.Sink.write(s, true, mode(), c); return true; } };
    }

    public static void main(String[] args) throws Exception {
        for (String setup : List.of("default pool, BLOCKING", "default pool, NON_BLOCKING", "reservedThreads=0, BLOCKING", "virtual threads, BLOCKING")) {
            QueuedThreadPool pool = new QueuedThreadPool();
            if (setup.startsWith("reservedThreads=0")) pool.setReservedThreads(0);
            if (setup.startsWith("virtual")) pool.setVirtualThreadsExecutor(VirtualThreads.getNamedVirtualThreadsExecutor("jetty-vt-"));
            Server server = new Server(pool);
            ServerConnector connector = new ServerConnector(server);
            connector.setHost("127.0.0.1");
            connector.setPort(0);
            server.addConnector(connector);
            server.setHandler(handler(setup.endsWith("NON_BLOCKING")));
            server.start();
            URI uri = URI.create("http://127.0.0.1:" + connector.getLocalPort() + "/");
            CLIENT.send(HttpRequest.newBuilder(uri).build(), HttpResponse.BodyHandlers.ofString());   // warm up the connection
            System.out.printf("%-28s -> %s%n", setup, CLIENT.send(HttpRequest.newBuilder(uri).build(), HttpResponse.BodyHandlers.ofString()).body());
            server.stop();
        }
    }
}

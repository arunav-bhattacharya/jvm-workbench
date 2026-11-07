package workbench.nio.l05;

import io.vertx.core.Vertx;
import io.vertx.core.VertxOptions;
import io.vertx.core.http.HttpServer;

import java.net.URI;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.TreeSet;
import java.util.concurrent.Callable;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.TimeUnit;

/** One event loop, an HTTP server, 4 concurrent requests that each make a 500 ms "JDBC call". Three ways. */
public class ExecuteBlockingDemo {
    public static void main(String[] args) throws Exception {
        for (String mode : List.of("block-on-event-loop", "executeBlocking-ordered", "executeBlocking-unordered")) {
            Vertx vertx = Vertx.vertx(new VertxOptions().setEventLoopPoolSize(1));
            Callable<String> fakeJdbc = () -> {
                Thread.sleep(500);
                return Thread.currentThread().getName();
            };
            HttpServer server = vertx.createHttpServer().requestHandler(req -> {
                switch (mode) {
                    case "block-on-event-loop" -> {
                        try {
                            req.response().end(fakeJdbc.call());                       // blocks the loop
                        } catch (Exception e) {
                            req.response().setStatusCode(500).end();
                        }
                    }
                    case "executeBlocking-ordered" ->                                  // the default: ordered = true
                            vertx.executeBlocking(fakeJdbc).onComplete(ar -> req.response().end(ar.result()));
                    default ->
                            vertx.executeBlocking(fakeJdbc, false).onComplete(ar -> req.response().end(ar.result()));
                }
            }).listen(0, "127.0.0.1").toCompletionStage().toCompletableFuture().get();

            java.net.http.HttpClient client = java.net.http.HttpClient.newBuilder()
                    .proxy(java.net.http.HttpClient.Builder.NO_PROXY).build();
            URI uri = URI.create("http://127.0.0.1:" + server.actualPort() + "/");
            long t0 = System.nanoTime();
            List<CompletableFuture<HttpResponse<String>>> calls = new ArrayList<>();
            for (int i = 0; i < 4; i++) {
                calls.add(client.sendAsync(HttpRequest.newBuilder(uri).build(), HttpResponse.BodyHandlers.ofString()));
            }
            Set<String> threads = new TreeSet<>();
            for (var call : calls) threads.add(call.get(10, TimeUnit.SECONDS).body());
            System.out.printf("%-26s 4 requests x 500 ms -> %4d ms, ran on %s%n",
                    mode, (System.nanoTime() - t0) / 1_000_000, threads);
            vertx.close().toCompletionStage().toCompletableFuture().get();
        }
    }
}

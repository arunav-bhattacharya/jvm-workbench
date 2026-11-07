package workbench.nio.l06;

import io.vertx.core.Context;
import io.vertx.core.Future;
import io.vertx.core.Promise;
import io.vertx.core.Vertx;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.TimeUnit;

/** 200 requests arrive on one IO context; each makes a 100 ms blocking call. Worker pool vs a virtual thread each. */
public class VirtualVsWorkerDemo {
    public static void main(String[] args) throws Exception {
        Vertx vertx = Vertx.vertx();                      // default worker pool: 20 threads
        Context server = vertx.getOrCreateContext();      // where the requests arrive
        Thread.Builder virtualThreads = Thread.ofVirtual().name("vt-", 0);   // used only on the server's thread
        for (boolean virtual : new boolean[] {false, true}) {
            Set<String> threads = ConcurrentHashMap.newKeySet();
            List<Future<Object>> calls = new ArrayList<>();
            long t0 = System.nanoTime();
            for (int i = 0; i < 200; i++) {
                Promise<Object> done = Promise.promise();
                server.runOnContext(v -> {
                    Runnable blockingCall = () -> {
                        threads.add(Thread.currentThread().getName());
                        try {
                            Thread.sleep(100);            // JDBC, a card-issuer call...
                        } catch (InterruptedException ignored) { }
                        done.complete();
                    };
                    if (virtual) virtualThreads.start(blockingCall);   // like @RunOnVirtualThread
                    else vertx.executeBlocking(() -> { blockingCall.run(); return null; }, false);   // like @Blocking
                });
                calls.add(done.future());
            }
            Future.all(calls).toCompletionStage().toCompletableFuture().get(30, TimeUnit.SECONDS);
            System.out.printf("%-26s 200 calls x 100 ms -> %,5d ms on %d distinct threads%n",
                    virtual ? "virtual thread per call" : "worker pool (20 threads)",
                    (System.nanoTime() - t0) / 1_000_000, threads.size());
        }
        vertx.close().toCompletionStage().toCompletableFuture().get();
    }
}

package workbench.nio.l05;

import io.vertx.core.Vertx;

/** Blocks an event loop on purpose and lets Vert.x's blocked-thread checker complain. Arg: sleep ms (default 6000). */
public class BlockedThreadDemo {
    public static void main(String[] args) throws Exception {
        long sleepMs = args.length > 0 ? Long.parseLong(args[0]) : 6_000;
        Vertx vertx = Vertx.vertx();                       // all defaults: 2 s limit, checked every 1 s
        vertx.runOnContext(v -> {
            System.out.println("[handler] Thread.sleep(" + sleepMs + ") on " + Thread.currentThread().getName());
            try {
                Thread.sleep(sleepMs);                     // stands in for JDBC, a lock, a slow loop...
            } catch (InterruptedException ignored) { }
            System.out.println("[handler] woke up");
        });
        Thread.sleep(sleepMs + 300);
        vertx.close().toCompletionStage().toCompletableFuture().get();
    }
}

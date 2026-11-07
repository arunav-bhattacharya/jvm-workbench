package workbench.nio.l06;

import io.vertx.core.Context;
import io.vertx.core.Vertx;
import io.vertx.core.VertxOptions;

import java.util.concurrent.TimeUnit;

/**
 * A plain Vert.x instance configured the way Quarkus 3.40 configures its own, then blocked for 3 s.
 * Arg: sleep ms (default 3000).
 */
public class QuarkusLikeLoopDemo {
    public static void main(String[] args) throws Exception {
        long sleepMs = args.length > 0 ? Long.parseLong(args[0]) : 3_000;
        int cpus = Runtime.getRuntime().availableProcessors();
        long maxHeapMb = Runtime.getRuntime().maxMemory() / (1024 * 1024);
        int quarkusLoops = (int) Math.max(2, Math.min(maxHeapMb / 10, cpus));   // VertxCoreRecorder.calculateDefaultIOThreads
        System.out.println("plain Vert.x default event loops: " + VertxOptions.DEFAULT_EVENT_LOOP_POOL_SIZE
                + ", Quarkus 3.40 default: max(2, min(" + maxHeapMb + " MB / 10, " + cpus + " cpus)) = " + quarkusLoops);

        Vertx vertx = Vertx.vertx(new VertxOptions()
                .setEventLoopPoolSize(quarkusLoops)
                .setMaxEventLoopExecuteTime(2).setMaxEventLoopExecuteTimeUnit(TimeUnit.SECONDS)   // Quarkus: 2 s, like Vert.x
                .setWarningExceptionTime(2).setWarningExceptionTimeUnit(TimeUnit.SECONDS));       // Quarkus: 2 s, Vert.x: 5 s
        vertx.runOnContext(v -> {
            System.out.println("[endpoint] on " + Thread.currentThread().getName()
                    + ", Context.isOnEventLoopThread()=" + Context.isOnEventLoopThread());
            try {
                Thread.sleep(sleepMs);   // a JDBC call inside an endpoint that returns Uni
            } catch (InterruptedException ignored) { }
        });
        Thread.sleep(sleepMs + 300);
        vertx.close().toCompletionStage().toCompletableFuture().get();
    }
}

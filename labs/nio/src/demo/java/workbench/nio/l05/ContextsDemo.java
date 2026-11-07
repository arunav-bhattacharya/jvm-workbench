package workbench.nio.l05;

import io.vertx.core.Context;
import io.vertx.core.DeploymentOptions;
import io.vertx.core.Future;
import io.vertx.core.ThreadingModel;
import io.vertx.core.VerticleBase;
import io.vertx.core.Vertx;
import io.vertx.core.VertxOptions;

import java.util.List;
import java.util.concurrent.TimeUnit;

/** Where does a verticle's code run? One verticle per threading model, plus executeBlocking. */
public class ContextsDemo {
    static String where() {
        Thread t = Thread.currentThread();
        Context c = Vertx.currentContext();
        return t.getName() + (t.isVirtual() ? " (virtual)" : "")
                + " eventLoopCtx=" + c.isEventLoopContext() + " workerCtx=" + c.isWorkerContext();
    }

    public static void main(String[] args) throws Exception {
        System.out.println("default event loops: " + VertxOptions.DEFAULT_EVENT_LOOP_POOL_SIZE
                + " (cpus=" + Runtime.getRuntime().availableProcessors() + "), default worker pool: "
                + VertxOptions.DEFAULT_WORKER_POOL_SIZE);
        Vertx vertx = Vertx.vertx();
        for (ThreadingModel model : List.of(ThreadingModel.EVENT_LOOP, ThreadingModel.WORKER, ThreadingModel.VIRTUAL_THREAD)) {
            await(vertx.deployVerticle(new VerticleBase() {
                @Override
                public Future<?> start() {
                    System.out.println("[" + model + "] start() on " + where());
                    return Future.succeededFuture();
                }
            }, new DeploymentOptions().setThreadingModel(model)));
        }
        vertx.runOnContext(v -> vertx.executeBlocking(() -> Thread.currentThread().getName())
                .onSuccess(name -> System.out.println("[executeBlocking] callable ran on " + name
                        + ", onSuccess runs on " + Thread.currentThread().getName())));
        Thread.sleep(300);
        await(vertx.close());
    }

    static <T> T await(Future<T> f) throws Exception {
        return f.toCompletionStage().toCompletableFuture().get(5, TimeUnit.SECONDS);
    }
}

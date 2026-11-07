package workbench.nio.l05;

import io.vertx.core.DeploymentOptions;
import io.vertx.core.Future;
import io.vertx.core.VerticleBase;
import io.vertx.core.Vertx;
import io.vertx.core.eventbus.DeliveryOptions;
import io.vertx.core.eventbus.EventBus;
import io.vertx.core.eventbus.ReplyException;

import java.util.List;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

/** Point-to-point, publish/subscribe and the three ways a request can fail. */
public class EventBusDemo {
    static final AtomicInteger IDS = new AtomicInteger();

    public static class Greeter extends VerticleBase {
        final int id = IDS.incrementAndGet();

        @Override
        public Future<?> start() {
            EventBus eb = vertx.eventBus();
            eb.<String>consumer("greet", m -> m.reply("hello " + m.body() + " from instance#" + id
                    + " on " + Thread.currentThread().getName()));
            eb.<String>consumer("news", m -> System.out.println("   [news] instance#" + id + " got '" + m.body() + "'"));
            eb.<String>consumer("fail", m -> m.fail(42, "boom from instance#" + id));
            return eb.<String>consumer("silent", m -> { /* never replies */ }).completion();
        }
    }

    public static void main(String[] args) throws Exception {
        Vertx vertx = Vertx.vertx();
        EventBus eb = vertx.eventBus();
        await(vertx.deployVerticle(Greeter::new, new DeploymentOptions().setInstances(2)));

        for (int i = 0; i < 4; i++) System.out.println("request greet #" + i + " -> " + await(eb.<String>request("greet", "dev" + i)).body());

        System.out.println("publish news:");
        eb.publish("news", "release 1.0");
        Thread.sleep(200);

        for (String address : List.of("nobody", "fail")) {
            try {
                await(eb.request(address, "x"));
            } catch (ExecutionException e) {
                ReplyException re = (ReplyException) e.getCause();
                System.out.println("request " + address + " -> " + re.failureType() + " code=" + re.failureCode() + " message=" + re.getMessage());
            }
        }
        long t0 = System.nanoTime();
        try {
            await(eb.request("silent", "x", new DeliveryOptions().setSendTimeout(300)));
        } catch (ExecutionException e) {
            ReplyException re = (ReplyException) e.getCause();
            System.out.println("request silent (timeout 300 ms) -> " + re.failureType() + " after "
                    + (System.nanoTime() - t0) / 1_000_000 + " ms");
        }
        System.out.println("default request timeout: " + DeliveryOptions.DEFAULT_TIMEOUT + " ms");
        await(vertx.close());
    }

    static <T> T await(Future<T> f) throws Exception {
        return f.toCompletionStage().toCompletableFuture().get(5, TimeUnit.SECONDS);
    }
}

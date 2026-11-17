package workbench.nio.l05;

import io.vertx.core.DeploymentOptions;
import io.vertx.core.Future;
import io.vertx.core.Vertx;
import io.vertx.core.VertxOptions;
import io.vertx.core.eventbus.DeliveryOptions;
import io.vertx.core.eventbus.Message;
import io.vertx.core.eventbus.ReplyException;
import io.vertx.core.eventbus.ReplyFailure;
import io.vertx.core.json.JsonObject;
import io.vertx.junit5.VertxExtension;
import io.vertx.junit5.VertxTestContext;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.concurrent.TimeUnit;

import static org.assertj.core.api.Assertions.assertThat;

@ExtendWith(VertxExtension.class)
class VerticleTest {

    @BeforeEach
    void deploy(Vertx vertx, VertxTestContext tc) {
        // a Supplier, so each of the 2 instances is a new object with its own context
        vertx.deployVerticle(WeighingDesk::new, new DeploymentOptions().setInstances(2))
                .onComplete(tc.succeedingThenComplete());
    }

    static JsonObject parcel(String id, double kg) {
        return new JsonObject().put("parcel", id).put("kg", kg);
    }

    @Test
    @DisplayName("a parcel under the weight limit is accepted, on an event-loop thread")
    void accepts(Vertx vertx, VertxTestContext tc) {
        vertx.eventBus().<JsonObject>request(WeighingDesk.ADDRESS, parcel("P-17", 1.5))
                .onComplete(tc.succeeding(reply -> tc.verify(() -> {   // assertions inside verify, or a failure is lost
                    assertThat(reply.body().getString("status")).isEqualTo("ACCEPTED");
                    assertThat(reply.body().getString("parcel")).isEqualTo("P-17");
                    assertThat(reply.body().getString("thread")).startsWith("vert.x-eventloop-thread-");
                    tc.completeNow();
                })));
    }

    @Test
    @DisplayName("a parcel over the limit fails with a RECIPIENT_FAILURE, code 413")
    void refusesOverLimit(Vertx vertx, VertxTestContext tc) {
        vertx.eventBus().request(WeighingDesk.ADDRESS, parcel("P-18", 32.0))
                .onComplete(tc.failing(err -> tc.verify(() -> {
                    ReplyException re = (ReplyException) err;
                    assertThat(re.failureType()).isEqualTo(ReplyFailure.RECIPIENT_FAILURE);
                    assertThat(re.failureCode()).isEqualTo(413);
                    assertThat(re.getMessage()).isEqualTo("too heavy");
                    tc.completeNow();
                })));
    }

    @Test
    @DisplayName("two instances share the work, each on its own event loop")
    void instancesRunOnTheirOwnLoops(Vertx vertx, VertxTestContext tc) {
        List<Future<Message<JsonObject>>> replies = new ArrayList<>();
        for (int i = 0; i < 10; i++) {
            replies.add(vertx.eventBus().request(WeighingDesk.ADDRESS, parcel("P-" + i, 2.0)));
        }
        Future.all(replies).onComplete(tc.succeeding(all -> tc.verify(() -> {
            Set<String> threads = new HashSet<>();
            for (Future<Message<JsonObject>> r : replies) threads.add(r.result().body().getString("thread"));
            assertThat(threads).hasSize(2);
            tc.completeNow();
        })));
    }

    @Test
    @io.vertx.junit5.Timeout(value = 3, timeUnit = TimeUnit.SECONDS)   // not org.junit.jupiter.api.Timeout
    @DisplayName("a request to an address nobody serves fails fast with NO_HANDLERS")
    void noHandlers(Vertx vertx, VertxTestContext tc) {
        vertx.eventBus().request("desk.lost-property", parcel("P-19", 1.0), new DeliveryOptions().setSendTimeout(1_000))
                .onComplete(tc.failing(err -> tc.verify(() -> {
                    assertThat(((ReplyException) err).failureType()).isEqualTo(ReplyFailure.NO_HANDLERS);
                    tc.completeNow();
                })));
    }

    @Test
    @DisplayName("six price lookups overlap on workers and the event loop stays free")
    void priceLookupsDoNotBlockTheLoop() throws Exception {
        // our own Vertx with ONE event loop, so a blocked loop would stall everything
        Vertx vertx = Vertx.vertx(new VertxOptions().setEventLoopPoolSize(1));
        try {
            await(vertx.deployVerticle(new PriceDesk()));
            long t0 = System.nanoTime();
            List<Future<Message<Long>>> replies = new ArrayList<>();
            for (int i = 0; i < 6; i++) replies.add(vertx.eventBus().request(PriceDesk.ADDRESS, "parcel-" + i));

            // lag probe: how long does a trivial task wait for the (only) event loop?
            long p0 = System.nanoTime();
            long lagMs = await(Future.<Long>future(p -> vertx.runOnContext(v -> p.complete((System.nanoTime() - p0) / 1_000_000))));

            await(Future.all(replies));
            long totalMs = (System.nanoTime() - t0) / 1_000_000;
            for (Future<Message<Long>> r : replies) assertThat(r.result().body()).isEqualTo(1_250L);
            assertThat(lagMs).as("event loop lag while the lookups run, ms").isLessThan(150);
            assertThat(totalMs).as("6 lookups of 300 ms, total ms").isLessThan(1_000);
        } finally {
            await(vertx.close());
        }
    }

    static <T> T await(Future<T> f) throws Exception {
        return f.toCompletionStage().toCompletableFuture().get(10, TimeUnit.SECONDS);
    }
}

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
        vertx.deployVerticle(AuthorizeVerticle::new, new DeploymentOptions().setInstances(2))
                .onComplete(tc.succeedingThenComplete());
    }

    static JsonObject payment(String card, double amount) {
        return new JsonObject().put("card", card).put("amount", amount);
    }

    @Test
    @DisplayName("an authorization under the limit is approved, on an event-loop thread")
    void approves(Vertx vertx, VertxTestContext tc) {
        vertx.eventBus().<JsonObject>request(AuthorizeVerticle.ADDRESS, payment("4111", 120.00))
                .onComplete(tc.succeeding(reply -> tc.verify(() -> {   // assertions inside verify, or a failure is lost
                    assertThat(reply.body().getString("status")).isEqualTo("APPROVED");
                    assertThat(reply.body().getString("card")).isEqualTo("4111");
                    assertThat(reply.body().getString("thread")).startsWith("vert.x-eventloop-thread-");
                    tc.completeNow();
                })));
    }

    @Test
    @DisplayName("an authorization over the limit fails with a RECIPIENT_FAILURE, code 402")
    void declinesOverLimit(Vertx vertx, VertxTestContext tc) {
        vertx.eventBus().request(AuthorizeVerticle.ADDRESS, payment("4111", 900.00))
                .onComplete(tc.failing(err -> tc.verify(() -> {
                    ReplyException re = (ReplyException) err;
                    assertThat(re.failureType()).isEqualTo(ReplyFailure.RECIPIENT_FAILURE);
                    assertThat(re.failureCode()).isEqualTo(402);
                    assertThat(re.getMessage()).isEqualTo("limit exceeded");
                    tc.completeNow();
                })));
    }

    @Test
    @DisplayName("two instances share the work, each on its own event loop")
    void instancesRunOnTheirOwnLoops(Vertx vertx, VertxTestContext tc) {
        List<Future<Message<JsonObject>>> replies = new ArrayList<>();
        for (int i = 0; i < 10; i++) {
            replies.add(vertx.eventBus().request(AuthorizeVerticle.ADDRESS, payment("card-" + i, 10.00)));
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
        vertx.eventBus().request("payments.refund", payment("4111", 1.00), new DeliveryOptions().setSendTimeout(1_000))
                .onComplete(tc.failing(err -> tc.verify(() -> {
                    assertThat(((ReplyException) err).failureType()).isEqualTo(ReplyFailure.NO_HANDLERS);
                    tc.completeNow();
                })));
    }

    @Test
    @DisplayName("six balance queries overlap on workers and the event loop stays free")
    void balanceQueriesDoNotBlockTheLoop() throws Exception {
        // our own Vertx with ONE event loop, so a blocked loop would stall everything
        Vertx vertx = Vertx.vertx(new VertxOptions().setEventLoopPoolSize(1));
        try {
            await(vertx.deployVerticle(new BalanceVerticle()));
            long t0 = System.nanoTime();
            List<Future<Message<Long>>> replies = new ArrayList<>();
            for (int i = 0; i < 6; i++) replies.add(vertx.eventBus().request(BalanceVerticle.ADDRESS, "acct-" + i));

            // lag probe: how long does a trivial task wait for the (only) event loop?
            long p0 = System.nanoTime();
            long lagMs = await(Future.<Long>future(p -> vertx.runOnContext(v -> p.complete((System.nanoTime() - p0) / 1_000_000))));

            await(Future.all(replies));
            long totalMs = (System.nanoTime() - t0) / 1_000_000;
            for (Future<Message<Long>> r : replies) assertThat(r.result().body()).isEqualTo(12_500L);
            assertThat(lagMs).as("event loop lag while the queries run, ms").isLessThan(150);
            assertThat(totalMs).as("6 queries of 300 ms, total ms").isLessThan(1_000);
        } finally {
            await(vertx.close());
        }
    }

    static <T> T await(Future<T> f) throws Exception {
        return f.toCompletionStage().toCompletableFuture().get(10, TimeUnit.SECONDS);
    }
}

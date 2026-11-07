package workbench.nio.l05;

import io.vertx.core.Future;
import io.vertx.core.VerticleBase;

/**
 * Answers balance requests on {@link #ADDRESS}: the body is an account id, the reply is the
 * balance in cents as a {@code Long}.
 *
 * <p>It works, but it calls the blocking {@link LedgerDao} on the event loop, so six concurrent
 * requests take 6 x 300 ms and every other handler on that loop waits too. Fix it so the query runs
 * on a worker thread, the requests overlap, and the event loop stays free. Careful: one way of
 * doing that still runs the six queries one after another.
 */
public class BalanceVerticle extends VerticleBase {
    public static final String ADDRESS = "ledger.balance";

    @Override
    public Future<?> start() {
        return vertx.eventBus().<String>consumer(ADDRESS, msg -> {
            try {
                msg.reply(LedgerDao.balanceCents(msg.body()));   // BUG: a 300 ms blocking call on the event loop
            } catch (InterruptedException e) {
                msg.fail(500, "interrupted");
            }
        }).completion();
    }
}

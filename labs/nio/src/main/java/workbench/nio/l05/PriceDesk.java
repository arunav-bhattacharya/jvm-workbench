package workbench.nio.l05;

import io.vertx.core.Future;
import io.vertx.core.VerticleBase;

/**
 * The price desk: answers price requests on {@link #ADDRESS}. The body is a parcel id, the reply is
 * the postage in cents as a {@code Long}.
 *
 * <p>It works, but it calls the blocking {@link PriceBook} on the event loop, so six concurrent
 * requests take 6 x 300 ms and every other handler on that loop waits too. Fix it so the lookup runs
 * on a worker thread, the requests overlap, and the event loop stays free. Careful: one way of
 * doing that still runs the six lookups one after another.
 */
public class PriceDesk extends VerticleBase {
    public static final String ADDRESS = "desk.price";

    @Override
    public Future<?> start() {
        return vertx.eventBus().<String>consumer(ADDRESS, msg -> {
            try {
                msg.reply(PriceBook.postageCents(msg.body()));   // BUG: a 300 ms blocking call on the event loop
            } catch (InterruptedException e) {
                msg.fail(500, "interrupted");
            }
        }).completion();
    }
}

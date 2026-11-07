package workbench.nio.l05;

import io.vertx.core.Future;
import io.vertx.core.VerticleBase;

public class BalanceVerticle extends VerticleBase {
    public static final String ADDRESS = "ledger.balance";

    @Override
    public Future<?> start() {
        return vertx.eventBus().<String>consumer(ADDRESS, msg ->
                // ordered = false: calls from this context may run in parallel on the worker pool.
                // The default (ordered = true) would queue them one after another on this context.
                vertx.executeBlocking(() -> LedgerDao.balanceCents(msg.body()), false)
                        .onSuccess(msg::reply)                       // back on the event loop
                        .onFailure(e -> msg.fail(500, e.getMessage()))
        ).completion();
    }
}

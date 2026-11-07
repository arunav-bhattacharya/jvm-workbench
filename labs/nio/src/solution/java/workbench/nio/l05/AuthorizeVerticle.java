package workbench.nio.l05;

import io.vertx.core.Future;
import io.vertx.core.VerticleBase;
import io.vertx.core.json.JsonObject;

public class AuthorizeVerticle extends VerticleBase {
    public static final String ADDRESS = "payments.authorize";
    public static final double LIMIT = 500.00;

    @Override
    public Future<?> start() {
        return vertx.eventBus().<JsonObject>consumer(ADDRESS, msg -> {
            JsonObject req = msg.body();
            if (req.getDouble("amount") > LIMIT) {
                msg.fail(402, "limit exceeded");                 // the requester gets a ReplyException
                return;
            }
            msg.reply(new JsonObject()
                    .put("status", "APPROVED")
                    .put("card", req.getString("card"))
                    .put("thread", Thread.currentThread().getName()));   // always this instance's event loop
        }).completion();                                          // deployed only once the consumer is registered
    }
}

package workbench.nio.l05;

import io.vertx.core.Future;
import io.vertx.core.VerticleBase;
import io.vertx.core.json.JsonObject;

public class WeighingDesk extends VerticleBase {
    public static final String ADDRESS = "desk.weigh";
    public static final double LIMIT_KG = 20.0;

    @Override
    public Future<?> start() {
        return vertx.eventBus().<JsonObject>consumer(ADDRESS, msg -> {
            JsonObject parcel = msg.body();
            if (parcel.getDouble("kg") > LIMIT_KG) {
                msg.fail(413, "too heavy");                      // the requester gets a ReplyException
                return;
            }
            msg.reply(new JsonObject()
                    .put("status", "ACCEPTED")
                    .put("parcel", parcel.getString("parcel"))
                    .put("thread", Thread.currentThread().getName()));   // always this instance's event loop
        }).completion();                                          // deployed only once the consumer is registered
    }
}

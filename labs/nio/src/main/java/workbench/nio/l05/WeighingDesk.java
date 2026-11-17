package workbench.nio.l05;

import io.vertx.core.Future;
import io.vertx.core.VerticleBase;

/**
 * The post office's weighing desk: it accepts parcels over the event bus, up to a weight limit.
 *
 * <p>In {@link #start()}, register a consumer on {@link #ADDRESS} for {@code JsonObject} messages
 * like {@code {"parcel": "P-17", "kg": 1.5}} and return the consumer's {@code completion()}
 * future, so the deployment finishes only when the consumer is registered. For each message:
 * <ul>
 *   <li>weight up to {@link #LIMIT_KG}: reply with a {@code JsonObject}
 *       {@code {"status": "ACCEPTED", "parcel": <parcel>, "thread": <current thread name>}}</li>
 *   <li>weight above {@link #LIMIT_KG}: fail the message with code 413 and the text "too heavy"</li>
 * </ul>
 */
public class WeighingDesk extends VerticleBase {
    public static final String ADDRESS = "desk.weigh";
    public static final double LIMIT_KG = 20.0;

    @Override
    public Future<?> start() {
        throw new UnsupportedOperationException("TODO: register the consumer and return its completion()");
    }
}

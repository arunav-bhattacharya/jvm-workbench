package workbench.nio.l05;

import io.vertx.core.Future;
import io.vertx.core.VerticleBase;

/**
 * Authorizes card payments over the event bus.
 *
 * <p>In {@link #start()}, register a consumer on {@link #ADDRESS} for {@code JsonObject} messages
 * like {@code {"card": "4111", "amount": 120.00}} and return the consumer's {@code completion()}
 * future, so the deployment finishes only when the consumer is registered. For each message:
 * <ul>
 *   <li>amount up to {@link #LIMIT}: reply with a {@code JsonObject}
 *       {@code {"status": "APPROVED", "card": <card>, "thread": <current thread name>}}</li>
 *   <li>amount above {@link #LIMIT}: fail the message with code 402 and the text "limit exceeded"</li>
 * </ul>
 */
public class AuthorizeVerticle extends VerticleBase {
    public static final String ADDRESS = "payments.authorize";
    public static final double LIMIT = 500.00;

    @Override
    public Future<?> start() {
        throw new UnsupportedOperationException("TODO: register the consumer and return its completion()");
    }
}

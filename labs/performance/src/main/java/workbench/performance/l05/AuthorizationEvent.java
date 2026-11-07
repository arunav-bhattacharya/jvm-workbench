package workbench.performance.l05;

import jdk.jfr.Event;

/**
 * TODO: turn this into a JFR event that records one card authorization.
 *
 * <ul>
 *   <li>Name it {@code workbench.Authorization} with {@code @Name}, so recordings and tools can find it.</li>
 *   <li>Give it a {@code @Label} and put it in a {@code @Category} that includes {@code "Payments"}.</li>
 *   <li>Fields: {@code String merchant}, {@code long amountCents}, {@code boolean approved}, each with a {@code @Label}.</li>
 * </ul>
 * The event's own duration (begin/end) will cover the issuer call.
 */
public class AuthorizationEvent extends Event {
}

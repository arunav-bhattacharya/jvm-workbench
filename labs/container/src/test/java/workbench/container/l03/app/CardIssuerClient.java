package workbench.container.l03.app;

import workbench.container.l03.Retry;
import workbench.container.l03.Timed;

public interface CardIssuerClient {
    @Timed
    @Retry(attempts = 3, on = IssuerUnavailableException.class)
    String authorize(String pan, long amountMinor);

    /** Not intercepted: forwarded as it is. */
    long limitMinor(String pan);

    /** A default method: its call to authorize goes through the proxy. */
    default String authorizeSmall(String pan) {
        return authorize(pan, Math.min(limitMinor(pan), 5_000));
    }
}

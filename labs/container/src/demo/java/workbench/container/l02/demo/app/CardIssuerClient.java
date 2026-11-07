package workbench.container.l02.demo.app;

import workbench.container.l02.Retry;
import workbench.container.l02.Timed;

public interface CardIssuerClient {
    @Timed
    @Retry(attempts = 3, on = IssuerUnavailableException.class)
    String authorize(String pan, long amountMinor);

    @Timed
    @Retry(attempts = 3, on = IssuerUnavailableException.class)
    String capture(String authId);

    /** Two issuer calls in one default method. */
    default String authorizeAndCapture(String pan, long amountMinor) {
        return capture(authorize(pan, amountMinor));
    }
}

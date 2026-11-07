package workbench.container.l03.demo.app;

import workbench.container.l03.Retry;
import workbench.container.l03.Timed;

public interface CardIssuerClient {
    @Timed
    @Retry(attempts = 3, on = IssuerUnavailableException.class)
    String authorize(String pan, long amountMinor);

    @Timed
    @Retry(attempts = 3, on = IssuerUnavailableException.class)
    String refund(String authId, long amountMinor);
}

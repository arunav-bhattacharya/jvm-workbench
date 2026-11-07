package workbench.container.l03.app;

import workbench.container.l03.Component;

import java.util.concurrent.atomic.AtomicInteger;

@Component
public class RateQuoter {
    public static final AtomicInteger CREATED = new AtomicInteger();
    private final SlowRates rates;

    public RateQuoter(SlowRates rates) {
        CREATED.incrementAndGet();
        this.rates = rates;
    }

    public SlowRates rates() { return rates; }
}

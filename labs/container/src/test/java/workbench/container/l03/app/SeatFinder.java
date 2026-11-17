package workbench.container.l03.app;

import workbench.container.l03.Component;

import java.util.concurrent.atomic.AtomicInteger;

@Component
public class SeatFinder {
    public static final AtomicInteger CREATED = new AtomicInteger();
    private final SlowPlan plan;

    public SeatFinder(SlowPlan plan) {
        CREATED.incrementAndGet();
        this.plan = plan;
    }

    public SlowPlan plan() { return plan; }
}

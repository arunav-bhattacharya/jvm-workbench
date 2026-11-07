package workbench.container.l03.app;

import workbench.container.l03.Component;

import java.util.concurrent.atomic.AtomicInteger;

@Component
public class SlowRates {
    public static final AtomicInteger CREATED = new AtomicInteger();

    public SlowRates() throws InterruptedException {
        CREATED.incrementAndGet();
        Thread.sleep(50);                 // slow, so racing threads overlap inside it
    }
}

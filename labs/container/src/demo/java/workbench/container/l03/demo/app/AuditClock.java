package workbench.container.l03.demo.app;

import workbench.container.l03.Component;

import java.time.Clock;
import java.time.Instant;

@Component
public class AuditClock {
    private final Clock clock = Clock.systemUTC();

    public Instant now() { return clock.instant(); }
}

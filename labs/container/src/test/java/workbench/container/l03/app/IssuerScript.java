package workbench.container.l03.app;

import workbench.container.l03.Component;

import java.util.concurrent.atomic.AtomicInteger;

@Component
public class IssuerScript {
    public final AtomicInteger failures = new AtomicInteger();
    public final AtomicInteger calls = new AtomicInteger();
}

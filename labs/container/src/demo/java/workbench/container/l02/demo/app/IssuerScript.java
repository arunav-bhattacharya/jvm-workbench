package workbench.container.l02.demo.app;

import workbench.container.l02.Component;

import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.atomic.AtomicInteger;

/** What the fake issuer should do, and every call it saw. */
@Component
public class IssuerScript {
    public final AtomicInteger captureFailures = new AtomicInteger();
    public final List<String> seen = new CopyOnWriteArrayList<>();
}

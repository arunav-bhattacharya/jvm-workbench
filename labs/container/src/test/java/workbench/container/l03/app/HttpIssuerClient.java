package workbench.container.l03.app;

import workbench.container.l03.Component;

@Component
public class HttpIssuerClient implements CardIssuerClient {
    private final IssuerConfig config;
    private final IssuerScript script;

    public HttpIssuerClient(IssuerConfig config, IssuerScript script) {
        this.config = config;
        this.script = script;
    }

    public IssuerConfig config() { return config; }

    @Override
    public String authorize(String pan, long amountMinor) {
        script.calls.incrementAndGet();
        if (script.failures.getAndDecrement() > 0) throw new IssuerUnavailableException("issuer timed out");
        return "auth-" + pan.substring(pan.length() - 4) + "-" + amountMinor;
    }

    @Override
    public long limitMinor(String pan) { return 250_000; }
}

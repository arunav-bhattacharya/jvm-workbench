package workbench.container.l03.demo.app;

import workbench.container.l03.Component;

@Component
public class HttpIssuerClient implements CardIssuerClient {
    private final IssuerConfig config;

    public HttpIssuerClient(IssuerConfig config) { this.config = config; }

    @Override
    public String authorize(String pan, long amountMinor) { return "auth-" + pan.substring(pan.length() - 4); }

    @Override
    public String refund(String authId, long amountMinor) { return "ref-" + authId; }
}

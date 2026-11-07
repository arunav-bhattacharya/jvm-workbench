package workbench.container.l02.demo.app;

import workbench.container.l02.Component;

@Component
public class FlakyIssuer implements CardIssuerClient {
    private final IssuerScript script;

    public FlakyIssuer(IssuerScript script) {
        this.script = script;
    }

    @Override
    public String authorize(String pan, long amountMinor) {
        script.seen.add("authorize");
        return "auth-" + pan.substring(pan.length() - 4);
    }

    @Override
    public String capture(String authId) {
        if (script.captureFailures.getAndDecrement() > 0) {
            script.seen.add("capture (timed out)");
            throw new IssuerUnavailableException("issuer timed out");
        }
        script.seen.add("capture");
        return "cap-" + authId;
    }
}

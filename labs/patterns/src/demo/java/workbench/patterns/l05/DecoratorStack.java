package workbench.patterns.l05;

import java.util.ArrayList;
import java.util.List;

/** Two decorators around a flaky issuer. Same pieces, two orders, two different behaviors. */
public class DecoratorStack {
    interface IssuerCall { String authorize(long amountMinor); }

    // the real client: fails twice, then succeeds
    static final class FlakyIssuer implements IssuerCall {
        private int calls;
        public String authorize(long amountMinor) {
            if (++calls <= 2) throw new IllegalStateException("issuer timeout #" + calls);
            return "A-" + amountMinor;
        }
    }

    // decorator 1: logs every call that passes through it
    record Logging(IssuerCall inner, List<String> log) implements IssuerCall {
        public String authorize(long amountMinor) {
            log.add("authorize " + amountMinor);
            return inner.authorize(amountMinor);
        }
    }

    // decorator 2: tries up to `attempts` times
    record Retrying(IssuerCall inner, int attempts) implements IssuerCall {
        public String authorize(long amountMinor) {
            RuntimeException last = null;
            for (int i = 1; i <= attempts; i++) {
                try {
                    return inner.authorize(amountMinor);
                } catch (RuntimeException e) {
                    last = e;
                }
            }
            throw last;
        }
    }

    public static void main(String[] args) {
        List<String> log = new ArrayList<>();
        IssuerCall retryOutside = new Retrying(new Logging(new FlakyIssuer(), log), 3);
        System.out.println("Retrying(Logging(issuer)): " + retryOutside.authorize(1_250) + ", log lines: " + log.size());

        log.clear();
        IssuerCall logOutside = new Logging(new Retrying(new FlakyIssuer(), 3), log);
        System.out.println("Logging(Retrying(issuer)): " + logOutside.authorize(1_250) + ", log lines: " + log.size());
    }
}

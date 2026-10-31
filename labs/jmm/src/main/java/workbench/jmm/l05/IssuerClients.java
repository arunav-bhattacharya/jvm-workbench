package workbench.jmm.l05;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.function.Function;

/**
 * One {@link IssuerClient} per card issuer, created on first use. Request threads call {@link #clientFor}.
 *
 * <p>The bug: get-then-put is check-then-act, so two threads asking for a new issuer at once both
 * connect, and one connection leaks. Make it create exactly one client per issuer.
 */
public class IssuerClients {
    private final Map<String, IssuerClient> clients = new ConcurrentHashMap<>();
    private final Function<String, IssuerClient> connect;

    public IssuerClients(Function<String, IssuerClient> connect) {
        this.connect = connect;
    }

    public IssuerClient clientFor(String issuerId) {
        IssuerClient c = clients.get(issuerId);       // check
        if (c == null) {
            c = connect.apply(issuerId);              // slow: opens a connection
            clients.put(issuerId, c);                 // act: may replace another thread's client
        }
        return c;
    }
}

package workbench.jmm.l05;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.function.Function;

public class IssuerClients {
    private final Map<String, IssuerClient> clients = new ConcurrentHashMap<>();
    private final Function<String, IssuerClient> connect;

    public IssuerClients(Function<String, IssuerClient> connect) {
        this.connect = connect;
    }

    public IssuerClient clientFor(String issuerId) {
        // one atomic call: the function runs at most once per absent key, and other callers
        // for the same key wait for its result instead of connecting themselves
        return clients.computeIfAbsent(issuerId, connect);
    }
}

package workbench.startup.l03;

import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Proxy;

/**
 * Builds the depot client as a JDK dynamic proxy, as declarative web clients do. In a native
 * image the proxy class must be listed in the metadata, with its interfaces in this exact order.
 * Don't change this class.
 */
public final class DepotClients {
    private DepotClients() {
    }

    public static DepotClient connect(String baseUrl) {
        InvocationHandler handler = (proxy, method, args) -> switch (method.getName()) {
            case "locate" -> "OUT FOR DELIVERY " + args[0];
            case "close" -> null;
            case "toString" -> "DepotClient(" + baseUrl + ")";
            case "hashCode" -> System.identityHashCode(proxy);
            case "equals" -> proxy == args[0];
            default -> throw new UnsupportedOperationException(method.getName());
        };
        return (DepotClient) Proxy.newProxyInstance(
                DepotClient.class.getClassLoader(),
                new Class<?>[] {DepotClient.class, AutoCloseable.class},   // the order matters
                handler);
    }
}

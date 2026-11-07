package workbench.startup.l03;

import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Proxy;

/**
 * Builds the issuer client as a JDK dynamic proxy, as declarative REST clients do. In a native
 * image the proxy class must be listed in the metadata, with its interfaces in this exact order.
 * Don't change this class.
 */
public final class IssuerClients {
    private IssuerClients() {
    }

    public static CardIssuerClient connect(String baseUrl) {
        InvocationHandler handler = (proxy, method, args) -> switch (method.getName()) {
            case "authorize" -> "APPROVED " + args[0];
            case "close" -> null;
            case "toString" -> "CardIssuerClient(" + baseUrl + ")";
            case "hashCode" -> System.identityHashCode(proxy);
            case "equals" -> proxy == args[0];
            default -> throw new UnsupportedOperationException(method.getName());
        };
        return (CardIssuerClient) Proxy.newProxyInstance(
                CardIssuerClient.class.getClassLoader(),
                new Class<?>[] {CardIssuerClient.class, AutoCloseable.class},   // the order matters
                handler);
    }
}

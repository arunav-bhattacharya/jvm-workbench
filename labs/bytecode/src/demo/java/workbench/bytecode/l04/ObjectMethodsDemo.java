package workbench.bytecode.l04;

import java.io.IOException;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Proxy;
import java.lang.reflect.UndeclaredThrowableException;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/** Two handler bugs: forwarding equals to the target, and throwing a checked exception the method doesn't declare. */
public class ObjectMethodsDemo {
    public interface IssuerClient {
        String authorize(String pan) throws IOException;   // declares IOException
        String status();                                   // declares nothing
    }

    static class RealIssuer implements IssuerClient {
        public String authorize(String pan) throws IOException { throw new IOException("issuer timed out after 120 ms"); }
        public String status() { return "UP"; }
    }

    static IssuerClient forwardingEverything(IssuerClient target) {
        return (IssuerClient) Proxy.newProxyInstance(IssuerClient.class.getClassLoader(), new Class<?>[]{IssuerClient.class},
                (proxy, m, args) -> {
                    try {
                        return m.invoke(target, args);   // equals and hashCode go to the target too
                    } catch (InvocationTargetException e) {
                        throw e.getCause();
                    }
                });
    }

    public static void main(String[] args) {
        IssuerClient p = forwardingEverything(new RealIssuer());
        System.out.println("p.equals(p): " + p.equals(p) + "   (target.equals(p) was asked)");
        List<IssuerClient> listeners = new ArrayList<>();
        listeners.add(p);
        System.out.println("listeners.remove(p) after listeners.add(p): " + listeners.remove(p) + ", size still " + listeners.size());
        Set<IssuerClient> set = new HashSet<>(listeners);
        System.out.println("HashSet.contains(p): " + set.contains(p) + "   (HashMap checks == before equals)");

        try {
            p.authorize("4111111111111111");
        } catch (IOException e) {
            System.out.println("declared IOException passes through: " + e.getMessage());
        }

        IssuerClient angry = (IssuerClient) Proxy.newProxyInstance(IssuerClient.class.getClassLoader(),
                new Class<?>[]{IssuerClient.class}, (proxy, m, a) -> { throw new IOException("connection reset"); });
        try {
            angry.status();
        } catch (UndeclaredThrowableException e) {
            System.out.println("undeclared IOException from status() -> UndeclaredThrowableException, cause: " + e.getCause());
        }
    }
}

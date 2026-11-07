package workbench.container.l02.demo;

import workbench.container.l02.Container;
import workbench.container.l02.ContainerException;
import workbench.container.l02.demo.app.CardIssuerClient;
import workbench.container.l02.demo.app.FlakyIssuer;
import workbench.container.l02.demo.app.IssuerScript;

import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Proxy;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/** The container's JDK proxy next to one whose handler forwards every method, equals included. */
public class ProxyIdentityDemo {
    public static void main(String[] args) {
        Container c = new Container(List.of(IssuerScript.class, FlakyIssuer.class));
        CardIssuerClient issuer = c.get(CardIssuerClient.class);
        System.out.println("bean class: " + issuer.getClass().getName() + " implements "
                + Arrays.stream(issuer.getClass().getInterfaces()).map(Class::getSimpleName).toList());
        report("container's handler", issuer);

        FlakyIssuer target = new FlakyIssuer(new IssuerScript());
        InvocationHandler forwardAll = (proxy, method, a) -> method.invoke(target, a);   // equals goes to the target too
        report("forward everything", (CardIssuerClient) Proxy.newProxyInstance(
                CardIssuerClient.class.getClassLoader(), new Class<?>[] {CardIssuerClient.class}, forwardAll));

        try {
            c.get(FlakyIssuer.class);
        } catch (ContainerException e) {
            System.out.println("get(FlakyIssuer.class): " + e.getMessage());
        }
    }

    static void report(String name, CardIssuerClient p) {
        List<CardIssuerClient> listeners = new ArrayList<>(List.of(p));
        System.out.printf("%-20s p.equals(p)=%s  listeners.remove(p)=%s  hashCode is identity=%s%n",
                name, p.equals(p), listeners.remove(p), p.hashCode() == System.identityHashCode(p));
    }
}

package workbench.startup.l03.demo;

import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Proxy;
import java.util.Arrays;

/** Builds two JDK dynamic proxies from the same two interfaces, in opposite orders. */
public class ProxyOrderDemo {
    public interface IssuerApi {
        String authorize(String paymentId);
    }

    public static void main(String[] args) {
        InvocationHandler handler = (proxy, method, a) ->
                method.getName().equals("authorize") ? "APPROVED " + a[0] : null;
        ClassLoader loader = ProxyOrderDemo.class.getClassLoader();

        Object first = Proxy.newProxyInstance(loader, new Class<?>[] {IssuerApi.class, AutoCloseable.class}, handler);
        Object second = Proxy.newProxyInstance(loader, new Class<?>[] {AutoCloseable.class, IssuerApi.class}, handler);
        Object again = Proxy.newProxyInstance(loader, new Class<?>[] {IssuerApi.class, AutoCloseable.class}, handler);

        System.out.println("first : " + first.getClass().getName() + " " + names(first.getClass()));
        System.out.println("second: " + second.getClass().getName() + " " + names(second.getClass()));
        System.out.println("same class for (A, B) and (B, A)? " + (first.getClass() == second.getClass()));
        System.out.println("same class for (A, B) twice?      " + (first.getClass() == again.getClass()));
        System.out.println(((IssuerApi) first).authorize("pay_81"));
    }

    static String names(Class<?> c) {
        return Arrays.toString(Arrays.stream(c.getInterfaces()).map(Class::getSimpleName).toArray());
    }
}

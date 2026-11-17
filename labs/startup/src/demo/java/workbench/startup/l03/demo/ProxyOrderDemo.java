package workbench.startup.l03.demo;

import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Proxy;
import java.util.Arrays;

/** Builds two JDK dynamic proxies from the same two interfaces, in opposite orders. */
public class ProxyOrderDemo {
    public interface DepotApi {
        String locate(String parcelId);
    }

    public static void main(String[] args) {
        InvocationHandler handler = (proxy, method, a) ->
                method.getName().equals("locate") ? "OUT FOR DELIVERY " + a[0] : null;
        ClassLoader loader = ProxyOrderDemo.class.getClassLoader();

        Object first = Proxy.newProxyInstance(loader, new Class<?>[] {DepotApi.class, AutoCloseable.class}, handler);
        Object second = Proxy.newProxyInstance(loader, new Class<?>[] {AutoCloseable.class, DepotApi.class}, handler);
        Object again = Proxy.newProxyInstance(loader, new Class<?>[] {DepotApi.class, AutoCloseable.class}, handler);

        System.out.println("first : " + first.getClass().getName() + " " + names(first.getClass()));
        System.out.println("second: " + second.getClass().getName() + " " + names(second.getClass()));
        System.out.println("same class for (A, B) and (B, A)? " + (first.getClass() == second.getClass()));
        System.out.println("same class for (A, B) twice?      " + (first.getClass() == again.getClass()));
        System.out.println(((DepotApi) first).locate("PX-1042"));
    }

    static String names(Class<?> c) {
        return Arrays.toString(Arrays.stream(c.getInterfaces()).map(Class::getSimpleName).toArray());
    }
}

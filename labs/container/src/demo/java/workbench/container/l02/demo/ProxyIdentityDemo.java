package workbench.container.l02.demo;

import workbench.container.l02.Container;
import workbench.container.l02.ContainerException;
import workbench.container.l02.demo.app.BookingClient;
import workbench.container.l02.demo.app.FlakyBooking;
import workbench.container.l02.demo.app.BookingScript;

import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Proxy;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/** The container's JDK proxy next to one whose handler forwards every method, equals included. */
public class ProxyIdentityDemo {
    public static void main(String[] args) {
        Container c = new Container(List.of(BookingScript.class, FlakyBooking.class));
        BookingClient booking = c.get(BookingClient.class);
        System.out.println("bean class: " + booking.getClass().getName() + " implements "
                + Arrays.stream(booking.getClass().getInterfaces()).map(Class::getSimpleName).toList());
        report("container's handler", booking);

        FlakyBooking target = new FlakyBooking(new BookingScript());
        InvocationHandler forwardAll = (proxy, method, a) -> method.invoke(target, a);   // equals goes to the target too
        report("forward everything", (BookingClient) Proxy.newProxyInstance(
                BookingClient.class.getClassLoader(), new Class<?>[] {BookingClient.class}, forwardAll));

        try {
            c.get(FlakyBooking.class);
        } catch (ContainerException e) {
            System.out.println("get(FlakyBooking.class): " + e.getMessage());
        }
    }

    static void report(String name, BookingClient p) {
        List<BookingClient> listeners = new ArrayList<>(List.of(p));
        System.out.printf("%-20s p.equals(p)=%s  listeners.remove(p)=%s  hashCode is identity=%s%n",
                name, p.equals(p), listeners.remove(p), p.hashCode() == System.identityHashCode(p));
    }
}

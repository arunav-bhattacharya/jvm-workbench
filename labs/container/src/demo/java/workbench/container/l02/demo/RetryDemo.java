package workbench.container.l02.demo;

import workbench.container.l02.Container;
import workbench.container.l02.demo.app.BookingClient;
import workbench.container.l02.demo.app.FlakyBooking;
import workbench.container.l02.demo.app.BookingScript;
import workbench.container.l02.demo.app.BookingUnavailableException;

import java.lang.reflect.InvocationHandler;
import java.lang.reflect.InvocationTargetException;
import java.lang.reflect.Proxy;
import java.util.List;

/** reserveAndConfirm, with one confirmation timing out: what does the booking service see? */
public class RetryDemo {
    public static void main(String[] args) {
        Container c = new Container(List.of(BookingScript.class, FlakyBooking.class));
        BookingScript script = c.get(BookingScript.class);
        script.confirmFailures.set(1);
        String result = c.get(BookingClient.class).reserveAndConfirm("C12", 12_000);
        System.out.println("container's proxy:  " + result + ", booking service saw " + script.seen);
        System.out.println("  timed calls: " + c.callLog().names());

        BookingScript naiveScript = new BookingScript();
        naiveScript.confirmFailures.set(1);
        FlakyBooking target = new FlakyBooking(naiveScript);
        InvocationHandler retryEverything = (proxy, method, a) -> {        // retries any method, default ones too
            for (int attempt = 1; ; attempt++) {
                try {
                    return method.invoke(target, a);                       // the default body runs on the target
                } catch (InvocationTargetException e) {
                    if (attempt == 3 || !(e.getCause() instanceof BookingUnavailableException)) throw e.getCause();
                }
            }
        };
        BookingClient naive = (BookingClient) Proxy.newProxyInstance(
                BookingClient.class.getClassLoader(), new Class<?>[] {BookingClient.class}, retryEverything);
        System.out.println("retry the shell:    " + naive.reserveAndConfirm("C12", 12_000)
                + ", booking service saw " + naiveScript.seen);
    }
}

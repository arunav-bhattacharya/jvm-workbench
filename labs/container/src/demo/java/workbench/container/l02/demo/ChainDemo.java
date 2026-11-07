package workbench.container.l02.demo;

import workbench.container.l02.CallLog;
import workbench.container.l02.Interceptor;
import workbench.container.l02.Invocation;
import workbench.container.l02.RetryInterceptor;
import workbench.container.l02.TimedInterceptor;

import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;
import java.util.function.LongSupplier;

/** One issuer call that fails twice, sent through the same two interceptors in both orders. */
public class ChainDemo {
    public static void main(String[] args) {
        AtomicLong ticks = new AtomicLong();
        LongSupplier clock = () -> ticks.addAndGet(10_000_000);          // a fake clock: 10 ms per read
        Interceptor shout = inv -> {                                      // a third interceptor, to watch proceed()
            System.out.println("    -> " + inv.getName());
            try { return inv.proceed(); } finally { System.out.println("    <- " + inv.getName()); }
        };

        for (String order : List.of("timed, retry", "retry, timed")) {
            CallLog log = new CallLog();
            Interceptor timed = new TimedInterceptor(log, clock);
            Interceptor retry = new RetryInterceptor(3, List.of(IllegalStateException.class));
            List<Interceptor> chain = order.startsWith("timed") ? List.of(timed, retry, shout) : List.of(retry, timed, shout);
            AtomicInteger calls = new AtomicInteger();
            System.out.println(order + ":");
            Object result = new Invocation("Issuer.authorize", new Object[] {"4111111111111111"}, chain, () -> {
                if (calls.incrementAndGet() < 3) throw new IllegalStateException("issuer timed out");   // fails twice
                return "auth-1111";
            }).proceed();
            System.out.println("  result " + result + " after " + calls.get() + " calls, log " + log.calls());
        }
    }
}

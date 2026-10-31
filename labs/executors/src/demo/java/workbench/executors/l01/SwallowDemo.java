package workbench.executors.l01;

import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;

/** The same failing task, sent once with execute and once with submit. Watch where the exception goes. */
public class SwallowDemo {
    public static void main(String[] args) throws Exception {
        try (ExecutorService pool = Executors.newFixedThreadPool(1)) {
            Runnable charge = () -> {
                System.out.println("charging on " + Thread.currentThread().getName());
                throw new IllegalStateException("card issuer returned 502");
            };

            System.out.println("--- execute ---");
            pool.execute(charge);
            Thread.sleep(200);                      // give the stack trace time to print

            System.out.println("--- submit ---");
            Future<?> f = pool.submit(charge);
            Thread.sleep(200);
            System.out.println("submit: nothing printed. isDone=" + f.isDone());

            System.out.println("--- get ---");
            try {
                f.get();
            } catch (ExecutionException e) {
                System.out.println("get() threw ExecutionException, cause: " + e.getCause());
            }
        }
    }
}

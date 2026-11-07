package workbench.kotlin.l01.demo;

import kotlin.Unit;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/**
 * Java twin of ModifiersDemo.kt. noinline and crossinline leave no trace in the method signature:
 * Java sees plain Function0 and Function1 parameters. Every Java lambda already behaves like a
 * crossinline one, because `return` in a Java lambda can only leave the lambda.
 */
public class ModifiersDemoJava {
    public static void main(String[] args) throws InterruptedException {
        // subscribe(Function1<? super String, Unit>, Function1<? super String, Unit>)
        ModifiersDemoKt.subscribe(
                line -> { System.out.println(line); return Unit.INSTANCE; },
                event -> { System.out.println("listener got " + event); return Unit.INSTANCE; });
        ModifiersDemoKt.getListeners().forEach(l -> l.invoke("payment-captured"));

        ExecutorService pool = Executors.newSingleThreadExecutor(r -> new Thread(r, "settlement-worker"));
        // runInBackground(Executor, Function0<Unit>)
        ModifiersDemoKt.runInBackground(pool, () -> {
            System.out.println("running on " + Thread.currentThread().getName());
            return Unit.INSTANCE;
        });
        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);
    }
}

package workbench.executors.l04;

import java.time.Duration;
import java.util.concurrent.CancellationException;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

public final class Futures {
    private Futures() {}

    public static <T> T getOrDefault(Future<T> future, Duration timeout, T fallback) throws InterruptedException {
        try {
            return future.get(timeout.toNanos(), TimeUnit.NANOSECONDS);  // 1. wait, but not forever
        } catch (TimeoutException e) {
            future.cancel(true);              // 2. we stopped waiting: ask the task to stop too
            return fallback;
        } catch (ExecutionException | CancellationException e) {
            return fallback;                  // 3. the task failed or was cancelled by someone else
        } catch (InterruptedException e) {
            future.cancel(true);              // 4. our caller wants us to stop: pass the request on
            throw e;                          //    and propagate, which keeps the interrupt visible
        }
    }

    public static String describe(Future<?> future) {
        // state() never blocks; resultNow()/exceptionNow() are safe once state() says so
        return switch (future.state()) {
            case RUNNING -> "running";
            case SUCCESS -> "success: " + future.resultNow();
            case FAILED -> "failed: " + future.exceptionNow().getMessage();
            case CANCELLED -> "cancelled";
        };
    }
}

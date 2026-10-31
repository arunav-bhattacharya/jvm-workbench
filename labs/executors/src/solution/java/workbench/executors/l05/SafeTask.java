package workbench.executors.l05;

import java.util.function.Consumer;

public final class SafeTask {
    private SafeTask() {}

    public static Runnable wrap(Runnable task, Consumer<? super RuntimeException> onError) {
        return () -> {
            try {
                task.run();
            } catch (RuntimeException e) {
                onError.accept(e);   // report it, and return normally so the schedule keeps going
            }
            // an Error (OutOfMemoryError, StackOverflowError) still propagates: nothing after it is trustworthy
        };
    }
}

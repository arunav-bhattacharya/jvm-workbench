// Java equivalent of HandMadeFlowOn.kt: "flowOn" by hand with an executor and a 64-slot
// BlockingQueue. The upstream runs on the executor; the consumer drains the queue on its own thread,
// so the consumer's stack holds the draining loop and none of the reader's frames.
package workbench.flows.l03;

import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.function.Consumer;

public class HandMadeFlowOnJava {
    private static final Object END = new Object();

    /** Runs upstream on executor, pushes its values through a queue, and delivers them on the caller's thread. */
    @SuppressWarnings("unchecked")
    static <T> void flowOn(ExecutorService executor, Consumer<Consumer<T>> upstream, Consumer<T> downstream)
            throws InterruptedException {
        BlockingQueue<Object> mailbox = new ArrayBlockingQueue<>(64);
        executor.execute(() -> {
            upstream.accept(value -> {
                try { mailbox.put(value); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
            });
            try { mailbox.put(END); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        });
        for (Object v = mailbox.take(); v != END; v = mailbox.take()) downstream.accept((T) v);   // the drain loop
    }

    public static void main(String[] args) throws InterruptedException {
        ExecutorService io = Executors.newSingleThreadExecutor(r -> new Thread(r, "io-thread"));
        Consumer<Consumer<String>> reader = emit -> {
            emit.accept("pay-1");
            System.out.println("emit pay-1 returned on " + Thread.currentThread().getName());
        };
        flowOn(io, reader, id -> {
            System.out.println("collected " + id + " on " + Thread.currentThread().getName());
            for (StackTraceElement f : Thread.currentThread().getStackTrace())
                System.out.println("    at " + f.getClassName().replace("workbench.flows.l03.", "") + "." + f.getMethodName());
        });
        io.shutdown();
    }
}

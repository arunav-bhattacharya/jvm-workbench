package workbench.patterns.l11;

import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

/** One producer, four consumers, a bounded queue, and one poison pill per consumer. */
public class ProducerConsumerDemo {
    sealed interface Msg permits Job, Stop {}
    record Job(int id) implements Msg {}
    record Stop() implements Msg {}

    public static void main(String[] args) throws Exception {
        int consumers = 4, jobs = 1_000;
        BlockingQueue<Msg> queue = new ArrayBlockingQueue<>(16);     // bounded: a full queue makes the producer wait
        AtomicInteger processed = new AtomicInteger();

        ExecutorService pool = Executors.newVirtualThreadPerTaskExecutor();
        for (int c = 0; c < consumers; c++) {
            pool.submit(() -> {
                while (true) {
                    Msg m = queue.take();
                    if (m instanceof Stop) return null;              // this consumer is done
                    processed.incrementAndGet();
                }
            });
        }

        for (int i = 0; i < jobs; i++) queue.put(new Job(i));
        for (int c = 0; c < consumers; c++) queue.put(new Stop());   // one pill PER consumer

        pool.shutdown();
        boolean finished = pool.awaitTermination(2, TimeUnit.SECONDS);
        System.out.println("processed " + processed + " of " + jobs + ", all consumers finished: " + finished);
        if (!finished) {
            pool.shutdownNow();                                      // interrupt the ones still blocked in take()
            System.out.println("some consumers never got a pill and were still waiting in take()");
        }
    }
}

package workbench.concurrency.l12;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Consumer;

public final class SettlementPipeline {
    // a pill no real record can be: compared by identity, so even a record "PILL" is just a record
    @SuppressWarnings("StringOperationCanBeSimplified")
    private static final String PILL = new String("PILL");

    private SettlementPipeline() {}

    public static int run(List<List<String>> perProducer, int consumers, int capacity, Consumer<String> process)
            throws InterruptedException {
        BlockingQueue<String> queue = new ArrayBlockingQueue<>(capacity);   // bounded: producers wait when it's full
        AtomicInteger processed = new AtomicInteger();

        // 1. consumers: take until a pill arrives
        List<Thread> consumerThreads = new ArrayList<>();
        for (int c = 0; c < consumers; c++) {
            Thread t = new Thread(() -> {
                try {
                    while (true) {
                        String record = queue.take();
                        if (record == PILL) return;          // identity, not equals
                        process.accept(record);
                        processed.incrementAndGet();
                    }
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }
            }, "settle-consumer-" + c);
            t.start();
            consumerThreads.add(t);
        }

        // 2. producers: put every record
        List<Thread> producerThreads = new ArrayList<>();
        for (List<String> records : perProducer) {
            Thread t = new Thread(() -> {
                try {
                    for (String r : records) queue.put(r);
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }
            });
            t.start();
            producerThreads.add(t);
        }

        // 3. only when every producer is done: one pill per consumer
        for (Thread t : producerThreads) t.join();
        for (int c = 0; c < consumers; c++) queue.put(PILL);

        // 4. wait for every consumer to stop before reporting
        for (Thread t : consumerThreads) t.join();
        return processed.get();
    }
}

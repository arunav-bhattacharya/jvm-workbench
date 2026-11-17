package workbench.patterns.l11;

import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

/** The packing rail: the counter clips order slips on, four packers take them off, and each packer needs its own "closed" card. */
public class ProducerConsumerDemo {
    sealed interface Card permits Slip, Closed {}
    record Slip(int orderNo) implements Card {}
    record Closed() implements Card {}                              // the poison pill: "the shop is closed, go home"

    public static void main(String[] args) throws Exception {
        int packers = 4, orders = 1_000;
        BlockingQueue<Card> rail = new ArrayBlockingQueue<>(16);     // bounded: a full rail makes the counter wait
        AtomicInteger packed = new AtomicInteger();

        ExecutorService team = Executors.newVirtualThreadPerTaskExecutor();
        for (int p = 0; p < packers; p++) {
            team.submit(() -> {
                while (true) {
                    Card c = rail.take();
                    if (c instanceof Closed) return null;            // this packer goes home
                    packed.incrementAndGet();
                }
            });
        }

        for (int i = 0; i < orders; i++) rail.put(new Slip(i));
        for (int p = 0; p < packers; p++) rail.put(new Closed());   // one card PER packer

        team.shutdown();
        boolean finished = team.awaitTermination(2, TimeUnit.SECONDS);
        System.out.println("packed " + packed + " of " + orders + ", all packers finished: " + finished);
        if (!finished) {
            team.shutdownNow();                                      // interrupt the ones still waiting in take()
            System.out.println("some packers never got a card and were still waiting at the rail");
        }
    }
}

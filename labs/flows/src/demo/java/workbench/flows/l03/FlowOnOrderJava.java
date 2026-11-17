// Java equivalent of FlowOnOrder.kt with flowOn: a reader thread puts items into a BlockingQueue
// with 64 slots, and the main thread takes them out and stores them. That queue is the channel
// that flowOn builds: the hatch in the wall.
package workbench.flows.l03;

import java.util.List;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;

public class FlowOnOrderJava {
    static final String END = "<end>";   // a queue can't be closed, so the reader sends an end marker

    public static void main(String[] args) throws InterruptedException {
        List<String> deliveryNote = List.of("flour,2000,g", "eggs,12,pcs", "milk,1000,ml");
        BlockingQueue<String> hatch = new ArrayBlockingQueue<>(64);

        Thread reader = new Thread(() -> {
            try {
                for (String line : deliveryNote) {
                    String item = line.substring(0, line.indexOf(','));
                    System.out.printf("read    %-6s on %s%n", item, Thread.currentThread().getName());
                    hatch.put(item);                   // blocks only when all 64 slots are full
                }
                hatch.put(END);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }, "io-thread");
        reader.start();

        for (String item = hatch.take(); !item.equals(END); item = hatch.take()) {
            Thread.sleep(30);                          // put it away and write it in the pantry book
            System.out.printf("stored  %-6s on %s%n", item, Thread.currentThread().getName());
        }
        reader.join();
    }
}

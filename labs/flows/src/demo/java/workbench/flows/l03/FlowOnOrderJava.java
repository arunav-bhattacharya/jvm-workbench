// Java equivalent of FlowOnOrder.kt with flowOn: a reader thread puts lines into a BlockingQueue
// with 64 slots, and the main thread takes them out and posts them. That queue is the channel
// that flowOn builds.
package workbench.flows.l03;

import java.util.List;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;

public class FlowOnOrderJava {
    static final String END = "<end>";   // a queue can't be closed, so the reader sends an end marker

    public static void main(String[] args) throws InterruptedException {
        List<String> lines = List.of("pay-1,4250,EUR", "pay-2,990,EUR", "pay-3,12000,GBP");
        BlockingQueue<String> mailbox = new ArrayBlockingQueue<>(64);

        Thread reader = new Thread(() -> {
            try {
                for (String line : lines) {
                    String id = line.substring(0, line.indexOf(','));
                    System.out.println("read    " + id + "   on " + Thread.currentThread().getName());
                    mailbox.put(id);                   // blocks only when all 64 slots are full
                }
                mailbox.put(END);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }, "io-thread");
        reader.start();

        for (String id = mailbox.take(); !id.equals(END); id = mailbox.take()) {
            Thread.sleep(30);                          // the ledger write
            System.out.println("posted  " + id + "   on " + Thread.currentThread().getName());
        }
        reader.join();
    }
}

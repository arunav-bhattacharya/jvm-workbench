// Java equivalent of ChannelFlowDemo.kt: Reactor's Flux.create gives a sink that several threads may
// call (it serializes them), much like channelFlow's send. We complete it only after both producer
// threads are done, which channelFlow does for you. One difference shows in the output: there is no
// mailbox here, so the subscriber runs on whichever producer thread calls next.
package workbench.flows.l03;

import reactor.core.publisher.Flux;

public class ChannelFlowDemoJava {
    static long t0;

    static void at(String s) {
        System.out.printf("  t=%3d %-46s thread=%s%n", System.currentTimeMillis() - t0, s, Thread.currentThread().getName());
    }

    static void sleep(long ms) {
        try { Thread.sleep(ms); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
    }

    public static void main(String[] args) {
        t0 = System.currentTimeMillis();
        Flux<String> both = Flux.create(sink -> {
            Thread north = Thread.ofVirtual().name("north-feed").start(() -> {
                for (int i = 0; i < 2; i++) { sleep(30); sink.next("north-" + i); at("sent north-" + i); }
            });
            Thread east = Thread.ofVirtual().name("east-feed").start(() -> {
                for (int i = 0; i < 2; i++) { sleep(45); sink.next("east-" + i); at("sent east-" + i); }
            });
            Thread.ofVirtual().start(() -> {
                try { north.join(); east.join(); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
                sink.complete();                       // channelFlow completes after its children by itself
            });
            at("create block returns (producers still running)");
        });
        both.doOnNext(v -> at("collect " + v)).blockLast();
        at("flux completed after both producers");
    }
}

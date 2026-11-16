// Java equivalent of FlowOnThreads.kt with Reactor: subscribeOn moves the source (the room behind
// the first wall), publishOn moves what follows it (the second wall), and toStream() hands the
// values back to the calling thread through a queue (the third room). Reactor moves downstream
// with publishOn; Flow's flowOn moves upstream.
package workbench.flows.l03;

import reactor.core.publisher.Flux;
import reactor.core.scheduler.Scheduler;
import reactor.core.scheduler.Schedulers;

public class FlowOnThreadsJava {
    static void log(String stage, Object v) {
        System.out.printf("  %-8s %-3s thread=%s%n", stage, v, Thread.currentThread().getName());
    }

    public static void main(String[] args) {
        Scheduler io = Schedulers.newSingle("io-thread");
        Scheduler cpu = Schedulers.newSingle("cpu-thread");

        Flux.range(1, 2)
            .doOnNext(i -> log("emit", i))
            .map(i -> { log("map1", i); return i; })
            .subscribeOn(io)
            .publishOn(cpu)
            .map(i -> { log("map2", i); return i; })
            .toStream()
            .forEach(i -> log("collect", i));

        io.dispose();
        cpu.dispose();
    }
}

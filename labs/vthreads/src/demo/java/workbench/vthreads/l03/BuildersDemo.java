package workbench.vthreads.l03;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.ThreadFactory;

/** Every way to start a virtual thread in JDK 21+, with what each one prints. */
public class BuildersDemo {
    static void show(String how) {
        Thread t = Thread.currentThread();
        System.out.printf("%-34s name=%-10s virtual=%-5s daemon=%s%n", how, "'" + t.getName() + "'", t.isVirtual(), t.isDaemon());
    }

    public static void main(String[] args) throws Exception {
        // 1. the shortcut: start one now, no name
        Thread a = Thread.startVirtualThread(() -> show("Thread.startVirtualThread"));
        a.join();

        // 2. the builder: name it, then start it
        Thread b = Thread.ofVirtual().name("auth-7").start(() -> show("Thread.ofVirtual().name().start"));
        b.join();

        // 3. unstarted: create now, start later
        Thread c = Thread.ofVirtual().unstarted(() -> show("Thread.ofVirtual().unstarted"));
        c.start();
        c.join();

        // 4. a factory with numbered names, for code that wants a ThreadFactory
        ThreadFactory factory = Thread.ofVirtual().name("ledger-", 0).factory();
        try (ExecutorService named = Executors.newThreadPerTaskExecutor(factory)) {
            for (int i = 0; i < 2; i++) named.submit(() -> show("newThreadPerTaskExecutor(factory)"));
        }

        // 5. the one you'll use most: a new virtual thread per task, closed with try-with-resources
        try (ExecutorService perTask = Executors.newVirtualThreadPerTaskExecutor()) {
            Future<String> f = perTask.submit(() -> {
                show("newVirtualThreadPerTaskExecutor");
                return "approved";
            });
            System.out.println("future result: " + f.get());
        }   // close() waits for every task submitted above
    }
}

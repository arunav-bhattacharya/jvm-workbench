package workbench.concurrency.l11;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.function.Function;

/**
 * Six requests on a pool of one reused thread. The handler sets the user only when the request
 * carries one. A pool of 1 makes the bug happen every time; a pool of 200 makes it rare and random.
 */
public class ThreadLocalBleed {
    static final ThreadLocal<String> USER = new ThreadLocal<>();

    static String leaky(String user) {
        if (user != null) USER.set(user);
        return "request(" + user + ") ran as " + USER.get();
    }

    static String clean(String user) {
        if (user != null) USER.set(user);
        try {
            return "request(" + user + ") ran as " + USER.get();
        } finally {
            USER.remove();                                   // leave the thread as you found it
        }
    }

    public static void main(String[] args) throws Exception {
        String[] requests = {"alice", null, "bob", null, null, "carol"};
        for (Function<String, String> handler : java.util.List.<Function<String, String>>of(ThreadLocalBleed::leaky, ThreadLocalBleed::clean)) {
            ExecutorService pool = Executors.newSingleThreadExecutor();
            System.out.println("---");
            for (String user : requests) System.out.println("  " + pool.submit(() -> handler.apply(user)).get());
            pool.shutdown();
        }
    }
}

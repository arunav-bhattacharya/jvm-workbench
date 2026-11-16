package workbench.performance.l08;

import java.lang.management.ManagementFactory;
import java.lang.management.ThreadInfo;
import java.lang.management.ThreadMXBean;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

// The "cpu=" column of a thread dump, read from inside the process: which platform threads used CPU in the last interval?
public class HotThreadsJava {
    record Hot(String name, long cpuNanos) { }

    static List<Hot> hottest(long millis, int n) throws InterruptedException {
        ThreadMXBean mx = ManagementFactory.getThreadMXBean();
        Map<Long, Long> before = new HashMap<>();
        for (long id : mx.getAllThreadIds()) before.put(id, mx.getThreadCpuTime(id));   // platform threads only
        Thread.sleep(millis);
        List<Hot> hot = new ArrayList<>();
        for (long id : mx.getAllThreadIds()) {
            Long then = before.get(id);
            long now = mx.getThreadCpuTime(id);                                         // -1 once a thread has died
            ThreadInfo info = mx.getThreadInfo(id);
            if (then != null && info != null && now > then) hot.add(new Hot(info.getThreadName(), now - then));
        }
        hot.sort(Comparator.comparingLong(Hot::cpuNanos).reversed());
        return hot.subList(0, Math.min(n, hot.size()));
    }

    public static void main(String[] args) throws InterruptedException {
        Thread spinner = Thread.ofPlatform().daemon().name("fee-recalc").start(() -> {
            long x = 1;
            while (true) x = x * 31 + 7;
        });
        for (Hot h : hottest(500, 3)) System.out.printf("%-20s %6.1f ms%n", h.name(), h.cpuNanos() / 1e6);
    }
}

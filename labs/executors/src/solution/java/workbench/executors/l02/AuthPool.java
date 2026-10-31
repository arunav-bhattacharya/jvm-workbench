package workbench.executors.l02;

import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

public final class AuthPool {
    private AuthPool() {}

    public static ThreadPoolExecutor create() {
        ThreadPoolExecutor pool = new ThreadPoolExecutor(
                4,                                  // core: kept even when idle
                8,                                  // max: only reached once the queue is full
                30, TimeUnit.SECONDS,               // idle threads above core retire after 30 s
                new ArrayBlockingQueue<>(16),       // bounded, so max and rejection can ever happen
                new ThreadPoolExecutor.AbortPolicy());  // the default, written out so readers see it
        pool.prestartAllCoreThreads();              // start the 4 core threads now, not on first use
        return pool;
    }
}

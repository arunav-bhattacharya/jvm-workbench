package workbench.executors.l09;

/** Where a pool reports a task that failed. */
public interface FailureLog {
    void failed(String requestId, String threadName, Throwable error);
}

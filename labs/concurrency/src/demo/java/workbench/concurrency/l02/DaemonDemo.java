package workbench.concurrency.l02;

/** A daemon thread does not keep the JVM alive. Its finally block does not run either. */
public class DaemonDemo {
    public static void main(String[] args) throws InterruptedException {
        Thread metrics = new Thread(() -> {
            try {
                for (int i = 1; ; i++) {
                    System.out.println("metrics: flush " + i);
                    Thread.sleep(200);
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            } finally {
                System.out.println("metrics: finally block ran");
            }
        }, "metrics-flusher");
        metrics.setDaemon(true);     // must be called before start(); try false
        metrics.start();

        Thread.sleep(700);
        System.out.println("main: done, returning");
    }
}

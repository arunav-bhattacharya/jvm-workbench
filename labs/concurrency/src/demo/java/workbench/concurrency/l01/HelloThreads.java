package workbench.concurrency.l01;

/** Lists the threads the JVM already has, then starts two of your own. Run it a few times. */
public class HelloThreads {
    public static void main(String[] args) throws InterruptedException {
        System.out.println("cores the JVM sees: " + Runtime.getRuntime().availableProcessors());
        System.out.println("Java threads before main starts any:");
        for (Thread t : Thread.getAllStackTraces().keySet()) {
            System.out.println("  " + t.getName() + (t.isDaemon() ? " (daemon)" : ""));
        }

        Runnable task = () -> System.out.println("hello from " + Thread.currentThread().getName());
        Thread a = new Thread(task, "worker-a");
        Thread b = new Thread(task, "worker-b");

        a.start();          // try changing these two calls to a.run() and b.run()
        b.start();

        a.join();           // wait for both to finish before main goes on
        b.join();
        System.out.println("main is done");
    }
}

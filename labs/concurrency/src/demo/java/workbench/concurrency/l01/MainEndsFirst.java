package workbench.concurrency.l01;

/** main returns at once. Does the program end? */
public class MainEndsFirst {
    public static void main(String[] args) {
        Thread worker = new Thread(() -> {
            for (int i = 1; i <= 5; i++) {
                System.out.println("worker: settling batch " + i);
                try {
                    Thread.sleep(300);
                } catch (InterruptedException e) {
                    return;
                }
            }
            System.out.println("worker: all batches settled");
        }, "settlement-worker");
        worker.start();
        System.out.println("main: returning from main()");
    }
}

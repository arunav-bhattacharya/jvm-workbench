package workbench.concurrency.l02;

/** Watch the interrupt flag: set by interrupt(), cleared when sleep() throws, restored by you. */
public class InterruptFlag {
    public static void main(String[] args) throws InterruptedException {
        Thread worker = new Thread(() -> {
            Thread me = Thread.currentThread();
            try {
                Thread.sleep(10_000);
            } catch (InterruptedException e) {
                System.out.println("1. caught InterruptedException, flag is now " + me.isInterrupted());
                me.interrupt();   // restore it: comment this line out and run again
                System.out.println("2. after interrupt(), flag is " + me.isInterrupted());
            }
            System.out.println("3. isInterrupted() only reads it:  " + me.isInterrupted());
            System.out.println("4. Thread.interrupted() reads AND clears: " + Thread.interrupted());
            System.out.println("5. so now the flag is " + me.isInterrupted());
        }, "worker");
        worker.start();
        Thread.sleep(200);
        worker.interrupt();          // a request, not a command
        worker.join();
    }
}

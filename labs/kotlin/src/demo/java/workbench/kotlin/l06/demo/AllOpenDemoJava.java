package workbench.kotlin.l06.demo;

/**
 * Java twin of AllOpenDemo.kt. Java classes are open unless you write final, so Java can extend the
 * Kotlin class only because all-open removed its final. Remove the marker and javac says:
 * "cannot inherit from final PrintQueue".
 */
public class AllOpenDemoJava {

    static final class LoggedPrintQueue extends PrintQueue {
        @Override
        public String print(String job) {
            System.out.println("  log: printing " + job);
            return super.print(job);
        }
    }

    public static void main(String[] args) {
        PrintQueue queue = new LoggedPrintQueue();
        System.out.println(queue.print("flyer.pdf"));
        AllOpenDemoKt.describe(PlainHelper.class);
    }
}

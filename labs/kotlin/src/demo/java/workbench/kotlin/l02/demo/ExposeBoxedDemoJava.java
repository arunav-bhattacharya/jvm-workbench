package workbench.kotlin.l02.demo;

/**
 * Java twin of ExposeBoxedDemo.kt. With @JvmExposeBoxed, Java gets a real constructor that runs the
 * init block, and boxed overloads of doubled() and describeFee().
 */
public class ExposeBoxedDemoJava {
    public static void main(String[] args) {
        Fee fee = new Fee(125);                                // runs init: validation is back
        System.out.println(ExposeBoxedDemoKt.describeFee(fee.doubled()));
        try {
            new Fee(-1);
        } catch (IllegalArgumentException e) {
            System.out.println("rejected: " + e.getMessage());
        }
    }
}

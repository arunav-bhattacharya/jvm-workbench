package workbench.kotlin.l02.demo;

/**
 * Java twin of ExposeBoxedDemo.kt. With @JvmExposeBoxed, Java gets a real constructor that runs the
 * init block, and boxed overloads of doubled() and describeRun().
 */
public class ExposeBoxedDemoJava {
    public static void main(String[] args) {
        Copies copies = new Copies(125);                       // runs init: validation is back
        System.out.println(ExposeBoxedDemoKt.describeRun(copies.doubled()));
        try {
            new Copies(-1);
        } catch (IllegalArgumentException e) {
            System.out.println("rejected: " + e.getMessage());
        }
    }
}

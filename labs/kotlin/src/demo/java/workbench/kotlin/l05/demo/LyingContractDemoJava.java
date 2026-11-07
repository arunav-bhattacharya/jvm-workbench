package workbench.kotlin.l05.demo;

/**
 * Java twin of LyingContractDemo.kt. Java's version of the same lie is a helper that answers true
 * and a cast that trusts it. In both languages the cast is the line that fails at run time.
 */
public class LyingContractDemoJava {

    static boolean lyingIsCaptured(PaymentEvent e) {
        return true;
    }

    public static void main(String[] args) {
        PaymentEvent failed = new Failed("pay_8", "insufficient funds");
        try {
            if (lyingIsCaptured(failed)) {
                Captured c = (Captured) failed;                  // Java makes you write the cast yourself
                System.out.println("captured " + c.getAmountMinor());
            }
        } catch (ClassCastException e) {
            System.out.println("ClassCastException: " + e.getMessage());
        }
        // the Kotlin function, seen from Java: just a boolean method, the contract is gone
        System.out.println("Kotlin lyingIsCaptured from Java: " + LyingContractDemoKt.lyingIsCaptured(failed));
    }
}

package workbench.kotlin.l05.demo;

/**
 * Java twin of LyingContractDemo.kt. Java's version of the same lie is a helper that answers true
 * and a cast that trusts it. In both languages the cast is the line that fails at run time.
 */
public class LyingContractDemoJava {

    static boolean lyingIsPrinted(JobEvent e) {
        return true;
    }

    public static void main(String[] args) {
        JobEvent jammed = new Jammed("job-8", "laser-1");
        try {
            if (lyingIsPrinted(jammed)) {
                Printed p = (Printed) jammed;                   // Java makes you write the cast yourself
                System.out.println("printed " + p.getPages() + " pages");
            }
        } catch (ClassCastException e) {
            System.out.println("ClassCastException: " + e.getMessage());
        }
        // the Kotlin function, seen from Java: just a boolean method, the contract is gone
        System.out.println("Kotlin lyingIsPrinted from Java: " + LyingContractDemoKt.lyingIsPrinted(jammed));
    }
}

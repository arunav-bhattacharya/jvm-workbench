package workbench.bytecode.l07;

/** The program the startup agent watches. */
public class AgentTarget {
    record Payment(String id, long amountMinor) {}

    public static void main(String[] args) {
        System.out.println("main: started");
        Payment p = new Payment("p-1", 1_250);    // Payment is loaded here, on first use
        System.out.println("main: " + p);
    }
}

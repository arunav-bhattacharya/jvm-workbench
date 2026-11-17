package workbench.bytecode.l07;

/** The program the startup agent watches. */
public class AgentTarget {
    record Ticket(String show, String seat) {}

    public static void main(String[] args) {
        System.out.println("main: started");
        Ticket t = new Ticket("Hamlet", "B12");   // Ticket is loaded here, on first use
        System.out.println("main: " + t);
    }
}

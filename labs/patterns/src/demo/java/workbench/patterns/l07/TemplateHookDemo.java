package workbench.patterns.l07;

import java.util.function.Supplier;

/** Template Method's sharpest edge, and the execute-around function that avoids it. */
public class TemplateHookDemo {

    // classic Template Method: a final skeleton with hooks for subclasses
    abstract static class OutboundCall {
        private final String label;

        OutboundCall() {
            label = "outbound " + name();           // calls a hook before the subclass has set its fields
        }

        final String execute() {                    // the skeleton
            System.out.println("  start " + label);
            try {
                return doCall();
            } finally {
                System.out.println("  end   " + label);
            }
        }

        abstract String name();                     // hook
        abstract String doCall();                   // hook
    }

    static final class ChargeCall extends OutboundCall {
        private final String psp;

        ChargeCall(String psp) { this.psp = psp; }  // runs AFTER OutboundCall() has called name()

        String name() { return "charge via " + psp; }
        String doCall() { return "ch_1250"; }
    }

    // execute around: the same skeleton as a function; the varying step is a parameter
    static <T> T outbound(String name, Supplier<T> body) {
        System.out.println("  start " + name);
        try {
            return body.get();
        } finally {
            System.out.println("  end   " + name);
        }
    }

    public static void main(String[] args) {
        System.out.println("template: " + new ChargeCall("northpay").execute());
        System.out.println("function: " + outbound("outbound charge via northpay", () -> "ch_1250"));
    }
}

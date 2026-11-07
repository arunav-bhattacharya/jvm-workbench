package workbench.startup.l04.demo;

import java.util.ArrayList;
import java.util.List;

/**
 * A toy checkpoint: three components register hooks in the order the service creates them.
 * Pass "leak" as an argument and the metrics reporter forgets to close its socket.
 */
public class HookOrderDemo {
    /** org.crac.Resource has the same two methods, each taking a Context argument. */
    interface Resource {
        void beforeCheckpoint();
        void afterRestore();
    }

    static final List<Resource> registered = new ArrayList<>();
    static final List<String> openSockets = new ArrayList<>();

    static final class Component implements Resource {
        final String name;
        final boolean leaks;

        Component(String name, boolean leaks) {
            this.name = name;
            this.leaks = leaks;
            openSockets.add(name);                       // every component holds a connection
            registered.add(this);                        // and registers itself when it is created
        }

        public void beforeCheckpoint() {
            System.out.println("  beforeCheckpoint: " + name);
            if (!leaks) openSockets.remove(name);
        }

        public void afterRestore() {
            System.out.println("  afterRestore:     " + name);
            if (!openSockets.contains(name)) openSockets.add(name);
        }
    }

    public static void main(String[] args) {
        boolean leak = args.length > 0 && args[0].equals("leak");
        new Component("ledger DB pool", false);         // created first: the others use it
        new Component("Kafka consumer", false);
        new Component("metrics reporter", leak);

        System.out.println("checkpoint requested");
        for (Resource r : registered.reversed()) r.beforeCheckpoint();         // last registered first
        if (openSockets.isEmpty()) {
            System.out.println("  -- snapshot written --");
        } else {
            System.out.println("  -- checkpoint refused, still open: " + openSockets + " --");
        }
        for (Resource r : registered) r.afterRestore();                       // first registered first
    }
}
